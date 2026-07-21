import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";

vi.mock("../api/tvDashboardApi", () => ({
  listDataRoutes: vi.fn(),
  previewDataBlockV2: vi.fn(),
  adminMediaUrl: vi.fn(),
  uploadPlaylistMedia: vi.fn(),
}));

import { listDataRoutes, previewDataBlockV2 } from "../api/tvDashboardApi";

const mockedRoutes = vi.mocked(listDataRoutes);
const mockedPreview = vi.mocked(previewDataBlockV2);

function renderPanel() {
  const onChange = vi.fn();
  return render(
    <ComunicadoEditorProvider playlistId="pl-1" value={{ blocks: [] }} onChange={onChange}>
      <DataRoutesSidePanel />
    </ComunicadoEditorProvider>,
  );
}

function clickCatalogCard(label: string) {
  const card = Array.from(document.querySelectorAll(".delpi-ui-data-route-catalog__card")).find((el) =>
    (el.textContent ?? "").includes(label),
  );
  expect(card).toBeTruthy();
  fireEvent.click(card!);
}

describe("DataRoutesSidePanel", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    mockedRoutes.mockResolvedValue([
      {
        operationId: "get_oee",
        label: "OEE geral",
        category: "production",
        description: "Indicador consolidado de eficiência.",
        metaShape: "scalar",
        allowedDisplayModes: ["kpi"],
        paramSchema: { periodDays: { type: "integer", label: "Dias", default: 7 } },
      },
    ]);
    mockedPreview.mockResolvedValue({
      block: {
        resolved: { kpi: { label: "OEE geral", value: 88.5 } },
      },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);
  });

  it("lista rotas e abre formulário após confirmar a fonte", async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText("Fontes de dados")).toBeTruthy());
    expect(screen.getByText("OEE geral")).toBeTruthy();
    expect(screen.getByText(/Indicador consolidado/)).toBeTruthy();
    clickCatalogCard("OEE geral");
    expect(screen.getByRole("complementary", { name: /Detalhe: OEE geral/ })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Usar esta fonte" }));
    expect(screen.getByLabelText("Rótulo")).toBeTruthy();
    expect(screen.getByText(/Indicador consolidado/)).toBeTruthy();
    expect(screen.getByText("Continuar")).toBeTruthy();
  });

  it("wizard pergunta o visual antes de inserir", async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText("Fontes de dados")).toBeTruthy());
    clickCatalogCard("OEE geral");
    fireEvent.click(screen.getByRole("button", { name: "Usar esta fonte" }));
    fireEvent.click(screen.getByText("Continuar"));
    expect(screen.getByText("Como apresentar?")).toBeTruthy();
    expect(screen.getByText(/KPI \(cards/)).toBeTruthy();
    expect(screen.getByText("Texto")).toBeTruthy();
    expect(screen.getByText("Forma")).toBeTruthy();
    expect(screen.getByText("Inserir no palco")).toBeTruthy();
  });

  it("inserir como texto cria bloco text ligado à fonte", async () => {
    const onChange = vi.fn();
    render(
      <ComunicadoEditorProvider playlistId="pl-1" value={{ blocks: [] }} onChange={onChange}>
        <DataRoutesSidePanel />
      </ComunicadoEditorProvider>,
    );
    await waitFor(() => expect(screen.getByText("Fontes de dados")).toBeTruthy());
    clickCatalogCard("OEE geral");
    fireEvent.click(screen.getByRole("button", { name: "Usar esta fonte" }));
    fireEvent.click(screen.getByText("Continuar"));
    fireEvent.click(screen.getByText("Texto"));
    fireEvent.click(screen.getByText("Inserir no palco"));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    const lastCall = onChange.mock.calls.at(-1)?.[0] as {
      blocks?: Array<{ id: string; type: string; dataSourceId?: string }>;
    };
    const blocks = lastCall?.blocks ?? [];
    const types = blocks.map((block) => block.type);
    expect(types).toContain("data_source");
    expect(types).toContain("text");
    const text = blocks.find((block) => block.type === "text");
    const source = blocks.find((block) => block.type === "data_source");
    expect(text?.dataSourceId).toBe(source?.id);
  });

  it("inserir como forma cria bloco shape ligado à fonte", async () => {
    const onChange = vi.fn();
    render(
      <ComunicadoEditorProvider playlistId="pl-1" value={{ blocks: [] }} onChange={onChange}>
        <DataRoutesSidePanel />
      </ComunicadoEditorProvider>,
    );
    await waitFor(() => expect(screen.getByText("Fontes de dados")).toBeTruthy());
    clickCatalogCard("OEE geral");
    fireEvent.click(screen.getByRole("button", { name: "Usar esta fonte" }));
    fireEvent.click(screen.getByText("Continuar"));
    fireEvent.click(screen.getByText("Forma"));
    fireEvent.click(screen.getByText("Inserir no palco"));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    const lastCall = onChange.mock.calls.at(-1)?.[0] as {
      blocks?: Array<{ id: string; type: string; dataSourceId?: string }>;
    };
    const blocks = lastCall?.blocks ?? [];
    expect(blocks.map((block) => block.type)).toEqual(
      expect.arrayContaining(["data_source", "shape"]),
    );
    const shape = blocks.find((block) => block.type === "shape");
    const source = blocks.find((block) => block.type === "data_source");
    expect(shape?.dataSourceId).toBe(source?.id);
  });

  it("testar rota chama preview-block e mostra resultado", async () => {
    renderPanel();
    await waitFor(() => {
      expect(document.querySelector(".delpi-ui-data-route-catalog__card")).toBeTruthy();
    });
    clickCatalogCard("OEE geral");
    fireEvent.click(screen.getByRole("button", { name: "Testar rota" }));
    await waitFor(() => expect(mockedPreview).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByText("Resultado do teste")).toBeTruthy());
    expect(screen.getByText("88,5")).toBeTruthy();
    expect(mockedPreview.mock.calls[0]?.[0]?.block?.dataBinding?.displayMode).toBe("auto");
  });
});
