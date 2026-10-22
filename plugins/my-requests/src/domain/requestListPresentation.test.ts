import { describe, expect, it } from "vitest";

import {
  requestListRequesterName,
  requestListTitle,
} from "./requestListPresentation";
import type { RequestSummary } from "../types/requests";

function row(overrides: Partial<RequestSummary> = {}): RequestSummary {
  return {
    id: "r1",
    request_number: "REQ-2026-000015",
    type_code: "general-request",
    status: "in_progress",
    priority: "normal",
    version: 1,
    created_by_user_id: "u1",
    created_by_name: "Ana Silva",
    allowed_actions: [],
    ...overrides,
  };
}

describe("requestListTitle", () => {
  it("positive: Abertura de Chamado usa payload.title", () => {
    expect(
      requestListTitle(
        row({
          payload: { title: "Ajuste de roteiro OP 109645", description: "Detalhe…" },
        }),
      ),
    ).toBe("Ajuste de roteiro OP 109645");
  });

  it("sibling: emissão NF usa party_name", () => {
    expect(
      requestListTitle(
        row({
          type_code: "invoice-issuance",
          payload: { party_name: "Cliente ACME" },
        }),
      ),
    ).toBe("Cliente ACME");
  });

  it("negative: sem título/payload relevante retorna null", () => {
    expect(requestListTitle(row({ payload: {} }))).toBeNull();
    expect(requestListTitle(row({ payload: undefined }))).toBeNull();
  });
});

describe("requestListRequesterName", () => {
  it("positive: usa created_by_name", () => {
    expect(requestListRequesterName(row())).toBe("Ana Silva");
  });

  it("negative: vazio vira travessão", () => {
    expect(requestListRequesterName(row({ created_by_name: "  " }))).toBe("—");
  });
});
