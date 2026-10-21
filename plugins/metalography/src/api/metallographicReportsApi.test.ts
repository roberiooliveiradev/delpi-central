import { describe, expect, it } from "vitest";

import { formatApiError, HttpRequestError } from "./httpClient";
import { listQuery } from "./metallographicReportsApi";

describe("api contract", () => {
  it("builds the list query with the server parameter names", () => {
    expect(listQuery({
      page: 2,
      pageSize: 20,
      reportNumber: "MET-2026",
      conclusionResult: "nonconforming",
      reportDateFrom: "2026-10-01",
    })).toBe("?page=2&page_size=20&report_date_from=2026-10-01&report_number=MET-2026&conclusion_result=nonconforming");
  });

  it("maps auth and version conflicts without dropping the message", () => {
    expect(formatApiError(null, 401).message).toMatch(/Sessão/);
    expect(formatApiError({ message: "O relatório foi alterado por outra pessoa." }, 412).message).toMatch(/alterad/);
    const error = new HttpRequestError("conflito", 412, "VERSION_CONFLICT");
    expect(error.status).toBe(412);
  });
});
