import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createDowntimeReason,
  listDowntimeReasons,
  setDowntimeReasonActive,
  updateDowntimeReason,
  type DowntimeReason,
} from "../api/downtimeReasonsApi";
import { DelpiMesRequestError } from "../api/httpClient";
import { DowntimeReasonsPage } from "./DowntimeReasonsPage";

vi.mock("../api/downtimeReasonsApi", () => ({
  listDowntimeReasons: vi.fn(),
  createDowntimeReason: vi.fn(),
  updateDowntimeReason: vi.fn(),
  setDowntimeReasonActive: vi.fn(),
}));

const reason = (overrides: Partial<DowntimeReason> = {}): DowntimeReason => ({
  code: "machine_mechanical",
  label: "Falha mecânica",
  category: "machine",
  requiresNote: false,
  active: true,
  sortOrder: 10,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
  ...overrides,
});

const CATALOG = [
  reason(),
  reason({
    code: "material_shortage",
    label: "Falta de material",
    category: "material",
    requiresNote: true,
    sortOrder: 90,
  }),
  reason({ code: "setup", label: "Preparação", category: "setup", active: false, sortOrder: 5 }),
];

function renderPage() {
  return render(<DowntimeReasonsPage onBack={vi.fn()} />);
}

async function loaded() {
  await screen.findByText("machine_mechanical");
}

describe("DowntimeReasonsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listDowntimeReasons).mockResolvedValue({ items: CATALOG });
  });
  afterEach(() => cleanup());

  it("shows loading then renders active and inactive rows with counts", async () => {
    renderPage();
    expect(screen.getByText(/Carregando motivos de parada/)).toBeTruthy();
    await loaded();
    expect(screen.getByText("material_shortage")).toBeTruthy();
    expect(screen.getByText("Preparação")).toBeTruthy();
    expect(screen.getByText(/2 ativos/)).toBeTruthy();
    expect(screen.getByText(/3 no total/)).toBeTruthy();
    expect(screen.getAllByText("Ativo")).toHaveLength(2);
    expect(screen.getAllByText("Inativo")).toHaveLength(1);
    expect(screen.getByText("sistema")).toBeTruthy();
    expect(screen.queryByText(/defaultPlanned|defaultCountsAsAvailabilityLoss/)).toBeNull();
    expect(screen.queryByRole("button", { name: /Excluir/i })).toBeNull();
  });

  it("calls the list endpoint without a branch", async () => {
    renderPage();
    await loaded();
    expect(listDowntimeReasons).toHaveBeenCalledWith(expect.any(AbortSignal));
    expect(listDowntimeReasons).not.toHaveBeenCalledWith(expect.stringContaining("branch"));
  });

  it("shows the controlled error state and retries", async () => {
    vi.mocked(listDowntimeReasons)
      .mockRejectedValueOnce(new DelpiMesRequestError("Serviço indisponível", 503))
      .mockResolvedValueOnce({ items: CATALOG });
    renderPage();
    await screen.findByText("Não foi possível carregar os motivos de parada");
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    await loaded();
  });

  it("shows an empty state that is not an error", async () => {
    vi.mocked(listDowntimeReasons).mockResolvedValue({ items: [] });
    renderPage();
    await screen.findByText("Nenhum motivo cadastrado");
  });

  it("filters locally by code, label and category", async () => {
    renderPage();
    await loaded();
    const search = screen.getByPlaceholderText(/Buscar por código/);
    fireEvent.change(search, { target: { value: "material" } });
    expect(screen.queryByText("machine_mechanical")).toBeNull();
    expect(screen.getByText("material_shortage")).toBeTruthy();
    fireEvent.change(search, { target: { value: "mecânica" } });
    expect(screen.getByText("machine_mechanical")).toBeTruthy();
    fireEvent.change(search, { target: { value: "inexistente" } });
    await screen.findByText("Nenhum motivo encontrado");
  });

  it("filters by status locally", async () => {
    renderPage();
    await loaded();
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "inactive" } });
    expect(screen.queryByText("machine_mechanical")).toBeNull();
    expect(screen.getByText("Preparação")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "active" } });
    expect(screen.queryByText("Preparação")).toBeNull();
    expect(screen.getByText("machine_mechanical")).toBeTruthy();
  });

  it("creates a reason through the modal without active or OEE fields", async () => {
    vi.mocked(createDowntimeReason).mockImplementation(async (input) =>
      reason({ ...input, active: true }),
    );
    renderPage();
    await loaded();
    fireEvent.click(screen.getByRole("button", { name: /Novo motivo/ }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Código"), { target: { value: "FALTA_EMBALAGEM" } });
    fireEvent.change(within(dialog).getByLabelText("Descrição"), { target: { value: "Falta de embalagem" } });
    fireEvent.change(within(dialog).getByLabelText("Categoria"), { target: { value: "material" } });
    fireEvent.change(within(dialog).getByLabelText("Ordem de exibição"), { target: { value: "42" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Criar motivo" }));
    await waitFor(() =>
      expect(createDowntimeReason).toHaveBeenCalledWith({
        code: "falta_embalagem",
        label: "Falta de embalagem",
        category: "material",
        requiresNote: false,
        sortOrder: 42,
      }),
    );
    const body = vi.mocked(createDowntimeReason).mock.calls[0][0] as Record<string, unknown>;
    expect(body).not.toHaveProperty("active");
    expect(body).not.toHaveProperty("defaultPlanned");
    await screen.findByText("Motivo criado.");
    await screen.findByText("falta_embalagem");
  });

  it("keeps code read-only on edit and sends only editable fields", async () => {
    vi.mocked(updateDowntimeReason).mockImplementation(async (_code, input) =>
      reason({ ...CATALOG[0], ...input }),
    );
    renderPage();
    await loaded();
    const row = screen.getByText("machine_mechanical").closest("tr")!;
    fireEvent.click(within(row as HTMLElement).getByRole("button", { name: "Editar" }));
    const dialog = await screen.findByRole("dialog");
    const codeInput = within(dialog).getByLabelText("Código") as HTMLInputElement;
    expect(codeInput.readOnly).toBe(true);
    expect(codeInput.value).toBe("machine_mechanical");
    fireEvent.change(within(dialog).getByLabelText("Descrição"), { target: { value: "Falha mecânica crítica" } });
    fireEvent.click(within(dialog).getByLabelText(/Exige observação/));
    fireEvent.click(within(dialog).getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() =>
      expect(updateDowntimeReason).toHaveBeenCalledWith("machine_mechanical", {
        label: "Falha mecânica crítica",
        category: "machine",
        requiresNote: true,
        sortOrder: 10,
      }),
    );
    const body = vi.mocked(updateDowntimeReason).mock.calls[0][1] as Record<string, unknown>;
    expect(body).not.toHaveProperty("code");
    expect(body).not.toHaveProperty("active");
    await screen.findByText("Motivo atualizado.");
  });

  it("shows the BFF message on a 422 validation error", async () => {
    vi.mocked(createDowntimeReason).mockRejectedValue(
      new DelpiMesRequestError("A categoria informada é inválida.", 422),
    );
    renderPage();
    await loaded();
    fireEvent.click(screen.getByRole("button", { name: /Novo motivo/ }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Código"), { target: { value: "novo_motivo" } });
    fireEvent.change(within(dialog).getByLabelText("Descrição"), { target: { value: "Novo" } });
    fireEvent.change(within(dialog).getByLabelText("Categoria"), { target: { value: "invalida" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Criar motivo" }));
    await within(dialog).findByText("A categoria informada é inválida.");
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("shows the conflict message on duplicate code", async () => {
    vi.mocked(createDowntimeReason).mockRejectedValue(
      new DelpiMesRequestError("Já existe um motivo com este código.", 409),
    );
    renderPage();
    await loaded();
    fireEvent.click(screen.getByRole("button", { name: /Novo motivo/ }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Código"), { target: { value: "other" } });
    fireEvent.change(within(dialog).getByLabelText("Descrição"), { target: { value: "Duplicado" } });
    fireEvent.change(within(dialog).getByLabelText("Categoria"), { target: { value: "other" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Criar motivo" }));
    await within(dialog).findByText("Já existe um motivo com este código.");
  });

  it("asks for confirmation before deactivating and preserves history wording", async () => {
    vi.mocked(setDowntimeReasonActive).mockImplementation(async (code, active) =>
      reason({ ...CATALOG.find((item) => item.code === code)!, active }),
    );
    renderPage();
    await loaded();
    const row = screen.getByText("machine_mechanical").closest("tr")!;
    fireEvent.click(within(row as HTMLElement).getByRole("button", { name: "Desativar" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Desativar motivo\?/)).toBeTruthy();
    expect(within(dialog).getByText(/serão preservados/)).toBeTruthy();
    expect(setDowntimeReasonActive).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Desativar motivo" }));
    await waitFor(() => expect(setDowntimeReasonActive).toHaveBeenCalledWith("machine_mechanical", false));
    await screen.findByText("Motivo desativado.");
  });

  it("keeps the record active and shows the BFF message when setup deactivation returns 409", async () => {
    const setupReason = reason({ code: "setup", label: "Preparação", category: "setup" });
    vi.mocked(listDowntimeReasons).mockResolvedValue({ items: [setupReason] });
    vi.mocked(setDowntimeReasonActive).mockRejectedValue(
      new DelpiMesRequestError(
        "Este motivo é utilizado pela detecção automática de preparação e não pode ser desativado.",
        409,
      ),
    );
    renderPage();
    const row = (await screen.findByText("Preparação")).closest("tr")!;
    fireEvent.click(within(row as HTMLElement).getByRole("button", { name: "Desativar" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Desativar motivo" }));
    await within(dialog).findByText(/não pode ser desativado/);
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(within(row as HTMLElement).getByText("Ativo")).toBeTruthy();
  });

  it("reactivates without confirmation and shows feedback", async () => {
    vi.mocked(setDowntimeReasonActive).mockImplementation(async (code, active) =>
      reason({ ...CATALOG.find((item) => item.code === code)!, active }),
    );
    renderPage();
    await loaded();
    const row = screen.getByText("Preparação").closest("tr")!;
    fireEvent.click(within(row as HTMLElement).getByRole("button", { name: "Reativar" }));
    await waitFor(() => expect(setDowntimeReasonActive).toHaveBeenCalledWith("setup", true));
    await screen.findByText("Motivo reativado.");
  });

  it("disables the submit action while a mutation is in flight", async () => {
    let resolveCreate!: (value: DowntimeReason) => void;
    vi.mocked(createDowntimeReason).mockImplementation(
      () => new Promise<DowntimeReason>((resolve) => { resolveCreate = resolve; }),
    );
    renderPage();
    await loaded();
    fireEvent.click(screen.getByRole("button", { name: /Novo motivo/ }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Código"), { target: { value: "novo" } });
    fireEvent.change(within(dialog).getByLabelText("Descrição"), { target: { value: "Novo" } });
    fireEvent.change(within(dialog).getByLabelText("Categoria"), { target: { value: "other" } });
    const submit = within(dialog).getByRole("button", { name: "Criar motivo" });
    fireEvent.click(submit);
    await waitFor(() => expect((submit as HTMLButtonElement).disabled).toBe(true));
    expect(createDowntimeReason).toHaveBeenCalledTimes(1);
    fireEvent.click(submit);
    expect(createDowntimeReason).toHaveBeenCalledTimes(1);
    resolveCreate(reason({ code: "novo" }));
    await screen.findByText("Motivo criado.");
  });
});
