import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const listOptions = vi.fn();
const listAnalyses = vi.fn();

vi.mock("../../api/entryAuditApi", () => ({
  listEntryAuditOptions: (...args: unknown[]) => listOptions(...args),
  listEntryAuditAnalyses: (...args: unknown[]) => listAnalyses(...args),
  createEntryAuditAnalysis: vi.fn(),
  getEntryAuditAnalysis: vi.fn(),
}));

import { EntryAuditHomePage } from "./EntryAuditHomePage";

beforeEach(() => {
  listOptions.mockReset();
  listAnalyses.mockReset();
  listOptions.mockResolvedValue({
    branches: [{ code: "01", name: "Matriz" }],
    document_types: [{ code: "nfe", label: "NF-e", default: true }],
  });
  listAnalyses.mockResolvedValue({
    items: [],
    page: 1,
    page_size: 50,
    total: 0,
  });
});

describe("EntryAuditHomePage", () => {
  it("renderiza escopo real e estado vazio sem dados inventados", async () => {
    render(
      <EntryAuditHomePage basePath="/apps/controllership-finance" />,
    );

    expect(await screen.findByText("Auditoria de Entradas")).toBeTruthy();
    expect(screen.getByLabelText("Data inicial")).toBeTruthy();
    expect(screen.getByLabelText("Filiais")).toBeTruthy();
    expect(screen.getByText(/Nenhuma análise anterior/)).toBeTruthy();
    expect(screen.queryByText("%")).toBeNull();
  });
});
