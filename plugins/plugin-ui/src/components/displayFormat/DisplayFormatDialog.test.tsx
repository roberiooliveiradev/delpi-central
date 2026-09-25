import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

import type { DisplayFormatPreviewResponse } from "../../displayFormat";
import { DisplayFormatDialog } from "./DisplayFormatDialog";

afterEach(() => {
  cleanup();
});

function mockPayload(overrides: Partial<DisplayFormatPreviewResponse> = {}): DisplayFormatPreviewResponse {
  return {
    locale: "pt-BR",
    valueSource: "authoritative",
    value: "2025-09-24",
    categories: [
      { category: "date", label: "Data abreviada" },
      { category: "custom", label: "Personalizado" },
      { category: "general", label: "Geral" },
      { category: "number", label: "Número" },
    ],
    options: [
      {
        formatId: "date-short",
        category: "date",
        label: "Data curta",
        pattern: "dd/MM/yyyy",
        spec: { category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" },
        preview: "24/09/2025",
        convertible: true,
      },
      {
        formatId: "date-month-year",
        category: "date",
        label: "Mês/ano",
        pattern: "MM/yyyy",
        spec: { category: "date", presetId: "date-month-year", pattern: "mm/yyyy" },
        preview: "09/2025",
        convertible: true,
      },
    ],
    custom: {
      formatId: "custom",
      category: "custom",
      label: "Personalizado",
      pattern: '"R$" #.##0,00',
      spec: { category: "custom", presetId: "custom", pattern: '"R$" #.##0,00' },
      preview: "R$ 30,00",
      convertible: true,
    },
    ...overrides,
  };
}

describe("DisplayFormatDialog", () => {
  it("mostra preview por opção vindo do backend e atualiza o card Exemplo", async () => {
    const onApply = vi.fn();
    const loader = vi.fn(async () => mockPayload());
    const host = document.createElement("main");
    host.className = "delpi-ui";
    document.body.appendChild(host);

    render(
      <DisplayFormatDialog
        open
        onClose={() => undefined}
        spec={{ category: "date", presetId: "date-short", pattern: "dd/mm/yyyy" }}
        onApply={onApply}
        sampleValue="2025-09-24"
        semanticType="date"
        previewLoader={loader}
        target="textProjection"
        portalScopeClassName="delpi-ui"
      />,
      { container: host },
    );

    const types = await screen.findByRole("listbox", { name: "Tipo" });
    expect(within(types).getByText("24/09/2025")).toBeTruthy();
    expect(within(types).getByText("09/2025")).toBeTruthy();
    expect(within(types).getByText("MM/yyyy")).toBeTruthy();
    expect(loader).toHaveBeenCalled();

    fireEvent.click(within(types).getByRole("option", { name: /^09\/2025/ }));
    await waitFor(() => {
      const sample = screen.getByText("Exemplo").parentElement;
      expect(sample?.textContent).toContain("09/2025");
    });

    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ presetId: "date-month-year", pattern: "mm/yyyy" }),
    );
  });

  it("mostra estado não conversível e não aplica formato inválido", async () => {
    const onApply = vi.fn();
    const loader = vi.fn(async () =>
      mockPayload({
        value: "ABC",
        options: [
          {
            formatId: "date-month-year",
            category: "date",
            label: "Mês/ano",
            pattern: "MM/yyyy",
            spec: { category: "date", presetId: "date-month-year", pattern: "mm/yyyy" },
            preview: null,
            convertible: false,
            reasonCode: "PARSE_FAILED",
            reason: "Não foi possível interpretar o valor.",
          },
        ],
      }),
    );
    const host = document.createElement("main");
    host.className = "delpi-ui";
    document.body.appendChild(host);

    render(
      <DisplayFormatDialog
        open
        onClose={() => undefined}
        spec={{ category: "date", presetId: "date-month-year", pattern: "mm/yyyy" }}
        onApply={onApply}
        sampleValue="ABC"
        previewLoader={loader}
        target="textProjection"
        portalScopeClassName="delpi-ui"
      />,
      { container: host },
    );

    const types = await screen.findByRole("listbox", { name: "Tipo" });
    const option = within(types).getByRole("option", { name: /Não foi possível interpretar/ });
    expect((option as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onApply).not.toHaveBeenCalled();
  });

  it("preview personalizado usa loader do servidor (sem formatador local)", async () => {
    const onApply = vi.fn();
    const loader = vi.fn(async (req) =>
      mockPayload({
        custom: {
          formatId: "custom",
          category: "custom",
          label: "Personalizado",
          pattern: req.customPattern || '"R$" #.##0,00',
          spec: {
            category: "custom",
            presetId: "custom",
            pattern: req.customPattern || '"R$" #.##0,00',
          },
          preview: "R$ 30,00",
          convertible: true,
        },
      }),
    );
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
        previewLoader={loader}
        target="chartValue"
        portalScopeClassName="delpi-ui"
      />,
      { container: host },
    );

    const cats = await screen.findByRole("listbox", { name: "Categoria" });
    fireEvent.click(within(cats).getByRole("option", { name: "Personalizado" }));
    const mask = screen.getByPlaceholderText('"R$" #.##0,00');
    fireEvent.change(mask, { target: { value: '"R$" #.##0,00' } });
    await waitFor(() => expect(screen.getByText(/R\$\s*30,00/)).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));
    expect(onApply).toHaveBeenCalledWith(
      expect.objectContaining({ category: "custom", pattern: '"R$" #.##0,00' }),
    );
    expect(loader.mock.calls.some((call) => call[0].customPattern === '"R$" #.##0,00')).toBe(true);
  });

  it("clicar em categoria/tipo não fecha o modal", async () => {
    const onClose = vi.fn();
    const onApply = vi.fn();
    const loader = vi.fn(async () =>
      mockPayload({
        value: 0.2,
        options: [
          {
            formatId: "number-2",
            category: "number",
            label: "2 casas",
            pattern: "0,00",
            spec: { category: "number", presetId: "number-2", decimalPlaces: 2 },
            preview: "0,20",
            convertible: true,
          },
          {
            formatId: "number-compact",
            category: "number",
            label: "Compacto",
            pattern: null,
            spec: { category: "number", presetId: "number-compact" },
            preview: "0,2",
            convertible: true,
          },
        ],
      }),
    );
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
        previewLoader={loader}
        target="tableColumn"
        targetHint='Coluna "Qtd"'
        portalScopeClassName="delpi-ui"
      />,
      { container: host },
    );

    expect(screen.getByText(/Formatando: Coluna/)).toBeTruthy();
    const cats = await screen.findByRole("listbox", { name: "Categoria" });
    fireEvent.pointerDown(within(cats).getByRole("option", { name: "Número" }));
    fireEvent.click(within(cats).getByRole("option", { name: "Número" }));
    expect(onClose).not.toHaveBeenCalled();
    const types = await screen.findByRole("listbox", { name: "Tipo" });
    await waitFor(() => expect(within(types).getByText("0,20")).toBeTruthy());
    expect(screen.getByRole("dialog")).toBeTruthy();
  });
});
