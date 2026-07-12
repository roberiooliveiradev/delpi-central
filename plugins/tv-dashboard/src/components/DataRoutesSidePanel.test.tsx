import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { DataRoutesSidePanel } from "./DataRoutesSidePanel";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";

vi.mock("../api/tvDashboardApi", () => ({
  listDataRoutes: vi.fn(),
  previewDataBlockV2: vi.fn(),
  adminMediaUrl: vi.fn(),
  uploadPlaylistMedia: vi.fn(),
}));

import { listDataRoutes } from "../api/tvDashboardApi";

const mockedRoutes = vi.mocked(listDataRoutes);

function renderPanel() {
  const onChange = vi.fn();
  return render(
    <ComunicadoEditorProvider playlistId="pl-1" value={{ blocks: [] }} onChange={onChange}>
      <DataRoutesSidePanel />
    </ComunicadoEditorProvider>,
  );
}

describe("DataRoutesSidePanel", () => {
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
  });

  it("lista rotas e abre formulário de configuração", async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText("Fontes de dados")).toBeTruthy());
    expect(screen.getByText("OEE geral")).toBeTruthy();
    expect(screen.getByText(/Indicador consolidado/)).toBeTruthy();
    fireEvent.click(screen.getByText("OEE geral"));
    expect(screen.getByLabelText("Rótulo")).toBeTruthy();
    expect(screen.getByText(/Indicador consolidado/)).toBeTruthy();
    expect(screen.getByText("Inserir fonte de dados")).toBeTruthy();
  });
});
