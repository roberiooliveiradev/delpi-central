import {
  cleanup,
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

const listTemplatesMock = vi.fn();
const listEventsMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  listChecklistTemplates: (...args: unknown[]) =>
    listTemplatesMock(...args),
  listTemplateEvents: (...args: unknown[]) => listEventsMock(...args),
}));

import { ChecklistAdminEventsPage } from "./ChecklistAdminEventsPage";

const BASE = "/apps/controllership-finance";

const TEMPLATE = {
  template_id: "t-1",
  code: "monthly-closing-checklist",
  name: "Checklist mensal",
};

const EVENTS = [
  {
    event_id: "e-1",
    entity_id: "v-1",
    competence_id: null,
    event_type: "VERSION_PUBLISHED",
    actor_subject: "u-1",
    detail: { effective_from_period: "2026-05" },
    created_at: "2026-04-15T10:00:00Z",
    version: 1,
  },
  {
    event_id: "e-2",
    entity_id: "v-2",
    competence_id: null,
    event_type: "DRAFT_CREATED",
    actor_subject: "u-2",
    detail: {},
    created_at: "2026-04-20T09:00:00Z",
    version: 2,
  },
];

describe("ChecklistAdminEventsPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("lists template events with the honest actor fallback", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listEventsMock.mockResolvedValue(EVENTS);
    render(<ChecklistAdminEventsPage basePath={BASE} />);
    expect(await screen.findByText("Versão publicada")).toBeTruthy();
    expect(listEventsMock).toHaveBeenCalledWith(
      "t-1",
      undefined,
      expect.anything(),
    );
    expect(screen.getByText("Histórico do checklist")).toBeTruthy();
    expect(screen.getByText("Rascunho criado")).toBeTruthy();
    // UX-014 pendente: ator exibido pelo identificador técnico.
    expect(screen.getByText(/u-1/)).toBeTruthy();
    expect(screen.getByText(/u-2/)).toBeTruthy();
    // Detalhes disponíveis do evento são exibidos.
    expect(
      screen.getByText(/effective_from_period=2026-05/),
    ).toBeTruthy();
  });

  it("scopes events to a version when the route provides one", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listEventsMock.mockResolvedValue([EVENTS[0]]);
    render(<ChecklistAdminEventsPage basePath={BASE} version={1} />);
    expect(await screen.findByText("Versão publicada")).toBeTruthy();
    expect(listEventsMock).toHaveBeenCalledWith(
      "t-1",
      1,
      expect.anything(),
    );
    expect(screen.getByText("Histórico — versão v1")).toBeTruthy();
  });

  it("shows empty state when there are no events", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listEventsMock.mockResolvedValue([]);
    render(<ChecklistAdminEventsPage basePath={BASE} />);
    await waitFor(() =>
      expect(
        screen.getByText("Nenhum evento registrado."),
      ).toBeTruthy(),
    );
  });

  it("shows authorization error for 403", async () => {
    listTemplatesMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    render(<ChecklistAdminEventsPage basePath={BASE} />);
    await waitFor(() =>
      expect(screen.getByText(/Acesso restrito/)).toBeTruthy(),
    );
  });
});
