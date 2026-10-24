import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const listCompetencesMock = vi.fn();
const openCompetenceMock = vi.fn();
const listItemsMock = vi.fn();
const getItemMock = vi.fn();

vi.mock("../../api/competencesApi", () => ({
  listCompetences: (...args: unknown[]) => listCompetencesMock(...args),
  openCompetence: (...args: unknown[]) => openCompetenceMock(...args),
  listCompetenceItems: (...args: unknown[]) => listItemsMock(...args),
  getCompetenceItem: (...args: unknown[]) => getItemMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { ClosingChecklistPage } from "./ClosingChecklistPage";

const ITEM = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  sort_order: 1,
  sheet: "ELETRONICO",
  name: "Extratos bancários — conta 01",
  origin_kind: "EXTERNAL",
  recipient_area: "CONTABIL",
  applicability: "REQUIRED",
  branch_scope: "MATRIX",
  totvs_report_ref: "R13",
  state: "EXPECTED",
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ClosingChecklistPage", () => {
  it("sem período lista competências abertas", async () => {
    listCompetencesMock.mockResolvedValue([
      {
        competence_id: "c1",
        period: "2026-10",
        template_version_id: "v1",
        status: "OPEN",
        opened_at: "2026-10-01T10:00:00Z",
        item_count: 53,
      },
    ]);

    render(<ClosingChecklistPage />);
    await waitFor(() =>
      expect(screen.getByText("Competências abertas")).toBeTruthy(),
    );
    expect(screen.getByText(/2026-10/)).toBeTruthy();
  });

  it("sem período e sem competências exibe estado vazio", async () => {
    listCompetencesMock.mockResolvedValue([]);
    render(<ClosingChecklistPage />);
    await waitFor(() =>
      expect(screen.getByText(/Nenhuma competência aberta/)).toBeTruthy(),
    );
  });

  it("com período exibe os itens esperados do snapshot", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    render(<ClosingChecklistPage period="2026-10" />);
    await waitFor(() =>
      expect(screen.getByText("CK-E-01")).toBeTruthy(),
    );
    expect(screen.getByText("Esperado")).toBeTruthy();
    // «Esperado» nunca aparece como estado de entrega/validação.
    expect(screen.queryByText(/^Entregue$/)).toBeNull();
    expect(screen.queryByText(/^Validado$/)).toBeNull();
  });

  it("competência não aberta oferece abertura governada", async () => {
    listItemsMock.mockRejectedValue(
      new ApiError(404, "não aberta", "competence_not_opened"),
    );
    openCompetenceMock.mockResolvedValue({
      competence_id: "c1",
      period: "2026-10",
      status: "OPEN",
    });
    listItemsMock
      .mockRejectedValueOnce(
        new ApiError(404, "não aberta", "competence_not_opened"),
      )
      .mockResolvedValueOnce([ITEM]);

    render(<ClosingChecklistPage period="2026-10" />);
    await waitFor(() =>
      expect(screen.getByText(/Abrir competência/)).toBeTruthy(),
    );
    await fireEvent.click(screen.getByText(/Abrir competência/));
    await waitFor(() =>
      expect(openCompetenceMock).toHaveBeenCalledWith("2026-10"),
    );
  });

  it("erro genérico exibe banner com retry", async () => {
    listItemsMock.mockRejectedValue(new ApiError(503, "indisponível"));
    render(<ClosingChecklistPage period="2026-10" />);
    await waitFor(() =>
      expect(screen.getByText("Origem indisponível")).toBeTruthy(),
    );
  });

  it("destinatário pendente aparece como «A definir», nunca inventado", async () => {
    listItemsMock.mockResolvedValue([
      { ...ITEM, recipient_area: null, totvs_report_ref: null },
    ]);
    render(<ClosingChecklistPage period="2026-10" />);
    await waitFor(() => expect(screen.getByText("A definir")).toBeTruthy());
  });
});
