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

const listMock = vi.fn();

vi.mock("../../api/meApi", () => ({
  listMyTasks: (...args: unknown[]) => listMock(...args),
}));

import { MyTasksPage } from "./MyTasksPage";

const TASK_REVIEW = {
  id: "p5:v1:FISCAL",
  sourceType: "PACKAGE",
  sourceId: "v1",
  actionKind: "PACKAGE_REVIEW_REQUIRED",
  title: "Revisar pacote FISCAL (área FISCAL)",
  ownerPage: "packages",
  ownerState: "SUBMITTED",
  statusLabel: "PENDING_AREA_ACCEPTANCE",
  assigneeUserId: "u-1",
  context: {
    contextType: "competence",
    contextId: "2026-05",
    contextLabel: "Competência 2026-05",
  },
  pendingSince: "2026-05-20T10:00:00Z",
  sourceStatus: "SUBMITTED",
  deepLink: "/apps/controllership-finance/closing/packages/2026-05",
};

const TASK_PENDENCY = {
  ...TASK_REVIEW,
  id: "p4:pend-1",
  sourceType: "PENDENCY",
  actionKind: "PENDENCY_ACTION_REQUIRED",
  title: "Nota fiscal pendente",
  ownerPage: "pendencies",
  statusLabel: "OPEN",
  deepLink:
    "/apps/controllership-finance/closing/pendencies?period=2026-05",
};

function setupTasks(items: unknown[] = [TASK_REVIEW, TASK_PENDENCY]) {
  listMock.mockResolvedValue({
    items,
    total: items.length,
    source: "controllership-finance-api",
    selfOnly: true,
  });
}

describe("MyTasksPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renderiza a projeção self-only com tipos e deep links", async () => {
    setupTasks();
    render(<MyTasksPage />);
    await waitFor(() =>
      expect(screen.getByText("Nota fiscal pendente")).toBeTruthy(),
    );
    expect(
      screen.getByText("Revisar pacote FISCAL (área FISCAL)"),
    ).toBeTruthy();
    const links = screen.getAllByRole("link", { name: /^Abrir:/ });
    expect(links).toHaveLength(2);
    expect(
      links[0].getAttribute("href"),
    ).toContain("/closing/");
  });

  it("estado vazio honesto quando não há trabalho atribuído", async () => {
    setupTasks([]);
    render(<MyTasksPage />);
    await waitFor(() =>
      expect(
        screen.getByText(
          /Nenhuma pendência, revisão ou esclarecimento atribuído/,
        ),
      ).toBeTruthy(),
    );
  });

  it("mapeia erro de autorização sem vazar detalhe", async () => {
    listMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    render(<MyTasksPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/autorização para consultar suas tarefas/i),
      ).toBeTruthy(),
    );
  });

  it("filtro de competência alimenta a consulta", async () => {
    setupTasks();
    render(<MyTasksPage />);
    await screen.findByText("Nota fiscal pendente");
    const input = screen.getByLabelText(/competência/i);
    fireEvent.change(input, { target: { value: "2026-05" } });
    const refresh = await screen.findByRole("button", {
      name: /atualizar consulta/i,
    });
    fireEvent.click(refresh);
    await waitFor(() =>
      expect(listMock).toHaveBeenCalledWith({ period: "2026-05" }),
    );
  });
});
