import { beforeEach, describe, expect, it, vi } from "vitest";

const httpGetEnvelope = vi.fn();

vi.mock("./httpClient", () => ({
  httpGetEnvelope: (...args: unknown[]) => httpGetEnvelope(...args),
  httpPostEnvelope: vi.fn(),
  httpPutEnvelope: vi.fn(),
  httpPostFormEnvelope: vi.fn(),
  downloadAuthenticatedFile: vi.fn(),
}));

import { listAdminBudgetResponsibilities } from "./budgetPlanningApi";

describe("listAdminBudgetResponsibilities filtro de tipo", () => {
  beforeEach(() => {
    httpGetEnvelope.mockReset();
    httpGetEnvelope.mockResolvedValue({
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, has_more: false },
    });
  });

  it("envia responsibility_type na query string (server-side)", async () => {
    await listAdminBudgetResponsibilities({
      responsibility_type: "collaborator",
      page: 1,
    });
    expect(httpGetEnvelope).toHaveBeenCalledWith(
      expect.stringContaining("responsibility_type=collaborator"),
      expect.any(String),
      expect.anything(),
    );
  });
});
