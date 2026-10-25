import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/httpClient";

vi.mock(
  "@delpi/plugin-ui/index",
  async () => await import("../../test/pluginUiMock"),
);

const listCatalogsMock = vi.fn();
const listEntriesMock = vi.fn();
const createMock = vi.fn();
const updateMock = vi.fn();
const deactivateMock = vi.fn();
const reactivateMock = vi.fn();

vi.mock("../../api/catalogsApi", () => ({
  listCatalogs: (...args: unknown[]) => listCatalogsMock(...args),
  listCatalogEntries: (...args: unknown[]) =>
    listEntriesMock(...args),
  createCatalogEntry: (...args: unknown[]) => createMock(...args),
  updateCatalogEntry: (...args: unknown[]) => updateMock(...args),
  deactivateCatalogEntry: (...args: unknown[]) =>
    deactivateMock(...args),
  reactivateCatalogEntry: (...args: unknown[]) =>
    reactivateMock(...args),
}));

import { CatalogsAdminPage } from "./CatalogsAdminPage";

const ENTRY = {
  entry_id: "e-1",
  catalog_key: "REJECTION_REASON",
  code: "DOC_INCOMPLETE",
  label: "Documento incompleto",
  attributes: { severity: "high" },
  effective_from_period: null,
  active: true,
  revision: 1,
  created_by: "ana",
  created_at: "2026-05-01T10:00:00Z",
  updated_by: null,
  updated_at: null,
  deactivated_by: null,
  deactivated_at: null,
};

function setup() {
  listCatalogsMock.mockResolvedValue([
    { catalog_key: "REJECTION_REASON", active: 1, inactive: 0 },
    { catalog_key: "BANK_ACCOUNT", active: 0, inactive: 0 },
  ]);
  listEntriesMock.mockResolvedValue([ENTRY]);
}

describe("CatalogsAdminPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("lista catálogos e carrega entradas ao selecionar", async () => {
    setup();
    render(<CatalogsAdminPage />);
    const card = await screen.findByRole("button", {
      name: /Motivos de rejeição/,
    });
    fireEvent.click(card);
    await waitFor(() =>
      expect(listEntriesMock).toHaveBeenCalledWith(
        "REJECTION_REASON"),
    );
    expect(await screen.findByText("DOC_INCOMPLETE")).toBeTruthy();
    expect(screen.getByText("Documento incompleto")).toBeTruthy();
  });

  it("cria entrada com código, rótulo e atributos JSON", async () => {
    setup();
    render(<CatalogsAdminPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Motivos de rejeição/,
      }),
    );
    await screen.findByText("DOC_INCOMPLETE");
    fireEvent.change(screen.getByLabelText("Código da entrada"), {
      target: { value: "DOC_WRONG_PERIOD" },
    });
    fireEvent.change(screen.getByLabelText("Rótulo da entrada"), {
      target: { value: "Competência divergente" },
    });
    createMock.mockResolvedValue({
      ...ENTRY,
      code: "DOC_WRONG_PERIOD",
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Criar entrada" }),
    );
    await waitFor(() => expect(createMock).toHaveBeenCalled());
    const [key, payload] = createMock.mock.calls[0];
    expect(key).toBe("REJECTION_REASON");
    expect(payload.code).toBe("DOC_WRONG_PERIOD");
    expect(payload.label).toBe("Competência divergente");
  });

  it("desativa entrada com confirmação e revision", async () => {
    setup();
    render(<CatalogsAdminPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Motivos de rejeição/,
      }),
    );
    await screen.findByText("DOC_INCOMPLETE");
    fireEvent.click(
      screen.getByRole("button", { name: "Desativar" }),
    );
    deactivateMock.mockResolvedValue({ ...ENTRY, active: false });
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Desativar entrada",
      }),
    );
    await waitFor(() => expect(deactivateMock).toHaveBeenCalled());
    expect(deactivateMock.mock.calls[0]).toEqual([
      "REJECTION_REASON",
      "DOC_INCOMPLETE",
      1,
    ]);
  });

  it("mapeia forbidden sem vazar detalhe", async () => {
    listCatalogsMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    render(<CatalogsAdminPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/autorização para consultar os catálogos/i),
      ).toBeTruthy(),
    );
  });
});
