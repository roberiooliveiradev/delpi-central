import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./data/api/invoicePostingApi";
import * as meApi from "./data/api/meApi";

vi.mock("./data/api/invoicePostingApi");
vi.mock("./data/api/meApi");
vi.mock("@delpi/plugin-ui/index", () => ({
  UserDirectoryPicker: () => null,
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

describe("App deep link", () => {
  it("abre o detalhe quando a URL traz requestId", async () => {
    window.history.replaceState(
      {},
      "",
      "/apps/lancamento-notas-fiscais/filial-01?requestId=req-deep",
    );
    vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
      id: "u1",
      name: "User",
      email: "u@delpi.com.br",
      permissions: ["lancamento-notas-fiscais.view", "lancamento-notas-fiscais.view.filial-01"],
    });
    vi.mocked(api.getRequest).mockResolvedValue({
      request: {
        id: "req-deep",
        branch_code: "01",
        document_number: "000012078",
        document_match_key: "000012078",
        series: "",
        supplier_code: "000001",
        supplier_store: "01",
        supplier_name: "Alpha",
        supplier_short_name: null,
        issue_date: "2026-07-01",
        amount: 10,
        received_at: "2026-07-02T10:00:00+00:00",
        observation: null,
        status: "blocked",
        block_reason: "other",
        block_description: "pendência",
        created_by_user_id: "u1",
        created_by_name: "Criador",
        assignee_user_id: "u2",
        assignee_name: "Responsável",
        cancelled_at: null,
        cancelled_by_user_id: null,
        cancelled_by_name: null,
        cancel_justification: null,
        completion_source: null,
        sf1_recno: null,
        erp_entry_date: null,
        reconciled_at: null,
        divergence_alert: false,
        divergence_detected_at: null,
        divergence_detail: null,
        created_at: "2026-07-02T10:00:00+00:00",
        updated_at: "2026-07-02T10:00:00+00:00",
      },
      history: [],
      comments: [],
      allowed_actions: ["view"],
    } as never);

    render(
      <App pathname="/apps/lancamento-notas-fiscais/filial-01" getAccessToken={() => "t"} />,
    );

    await waitFor(() => expect(screen.getByTestId("detail-page")).toBeTruthy());
    expect(api.getRequest).toHaveBeenCalledWith("req-deep");
  });
});
