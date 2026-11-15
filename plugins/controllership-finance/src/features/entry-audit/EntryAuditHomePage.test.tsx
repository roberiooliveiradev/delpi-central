import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

afterEach(() => {
  cleanup();
});

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

    expect(
      await screen.findByRole("heading", { name: /Auditoria de Entradas/i }),
    ).toBeTruthy();
    expect(screen.getByLabelText("De")).toBeTruthy();
    expect(screen.getByLabelText("Até")).toBeTruthy();
    expect(screen.getByLabelText("Filiais")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: /Executar auditoria/i }),
    ).toBeTruthy();
    expect(
      await screen.findByText(/Nenhuma análise anterior/),
    ).toBeTruthy();
    expect(screen.queryByText("%")).toBeNull();
  });

  it("exibe erro do histórico sem mascarar como lista vazia e permite retry", async () => {
    listAnalyses.mockRejectedValue(new Error("Falha de rede no histórico"));

    render(
      <EntryAuditHomePage basePath="/apps/controllership-finance" />,
    );

    expect(
      await screen.findByRole("button", { name: /Tentar novamente/i }),
    ).toBeTruthy();
    expect(screen.getByText(/Falha de rede no histórico/)).toBeTruthy();
    expect(screen.queryByTestId("empty-state")).toBeNull();

    listAnalyses.mockReset();
    listAnalyses.mockResolvedValue({
      items: [],
      page: 1,
      page_size: 10,
      total: 0,
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Tentar novamente/i }),
    );
    expect(await screen.findByTestId("empty-state")).toBeTruthy();
    expect(screen.queryByText(/Falha de rede no histórico/)).toBeNull();
  });
});
