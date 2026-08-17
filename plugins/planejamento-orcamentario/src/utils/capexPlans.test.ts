import { describe, expect, it } from "vitest";
import { HttpRequestError } from "../api/httpClient";
import {
  canSubmitPlanStatus,
  extractIncompleteInvestments,
  isPlanEditable,
  isPlanIncompleteError,
  isPlanLocked,
  isPlanVersionConflictError,
  mapCapexPlanError,
  planStatusLabel,
  planSubmitterDisplayName,
  sumEstimatedAmounts,
} from "./capexPlans";

describe("capexPlans utils", () => {
  it("labels de status em português", () => {
    expect(planStatusLabel("draft")).toBe("Rascunho");
    expect(planStatusLabel("submitted")).toBe("Enviado para aprovação");
    expect(planStatusLabel("changes_requested")).toBe("Ajustes solicitados");
    expect(planStatusLabel("rejected")).toBe("Reprovado");
    expect(planStatusLabel("approved")).toBe("Aprovado");
  });

  it("exibe nome do responsável, nunca o UUID", () => {
    expect(
      planSubmitterDisplayName({
        submitted_by: "a2b41ad2-0d41-4faf-b5bd-2f97e56e77eb",
        submitted_by_name: "Maria Silva",
      }),
    ).toBe("Maria Silva");
    expect(
      planSubmitterDisplayName(
        { submitted_by: "a2b41ad2-0d41-4faf-b5bd-2f97e56e77eb" },
        [{ action: "submitted", actor_name: "João Souza" }],
      ),
    ).toBe("João Souza");
    expect(
      planSubmitterDisplayName({
        submitted_by: "a2b41ad2-0d41-4faf-b5bd-2f97e56e77eb",
      }),
    ).toBe("—");
  });

  it("editável em draft e changes_requested; plano nulo ≡ draft", () => {
    expect(isPlanEditable(null)).toBe(true);
    expect(isPlanEditable({ status: "draft" } as never)).toBe(true);
    expect(isPlanEditable({ status: "changes_requested" } as never)).toBe(true);
    expect(isPlanEditable({ status: "submitted" } as never)).toBe(false);
    expect(isPlanLocked({ status: "approved" } as never)).toBe(true);
    expect(canSubmitPlanStatus({ status: "draft" } as never)).toBe(true);
    expect(canSubmitPlanStatus({ status: "submitted" } as never)).toBe(false);
  });

  it("soma valores sem float", () => {
    expect(
      sumEstimatedAmounts([{ estimated_amount: "10.50" }, { estimated_amount: "1.50" }]),
    ).toBe("12.00");
  });

  it("detecta incompleto e conflito 409", () => {
    const incomplete = new HttpRequestError("falha", 422, {
      code: "budget_capex_plan_incomplete",
      meta: {
        incomplete_investments: [
          { id: "i1", description: "X", missing_fields: ["category_id"] },
        ],
      },
    });
    expect(isPlanIncompleteError(incomplete)).toBe(true);
    expect(extractIncompleteInvestments(incomplete)[0]?.id).toBe("i1");

    const conflict = new HttpRequestError("x", 409, {
      code: "budget_capex_plan_version_conflict",
    });
    expect(isPlanVersionConflictError(conflict)).toBe(true);
    expect(mapCapexPlanError(conflict)).toMatch(/outra sessão/i);
  });
});
