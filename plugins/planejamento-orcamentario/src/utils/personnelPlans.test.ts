import { describe, expect, it } from "vitest";

import { HttpRequestError } from "../api/httpClient";
import {
  canSubmitPersonnelPlanStatus,
  findDuplicatePositionName,
  isPersonnelPlanEditable,
  isPersonnelPlanVersionConflictError,
  isPersonnelVersionConflictError,
  mapPersonnelError,
  parseHeadcountInput,
  personnelPlanStatusLabel,
  personnelSaveStatusLabel,
  POSITION_NAME_MAX_LENGTH,
  validatePositionName,
} from "./personnelPlans";

describe("personnelPlans utils", () => {
  it("trim e acentos no cargo", () => {
    const ok = validatePositionName("  Analista de Qualidade  ");
    expect(ok).toEqual({ ok: true, name: "Analista de Qualidade" });
  });

  it("rejeita cargo vazio e acima do limite", () => {
    expect(validatePositionName("   ").ok).toBe(false);
    expect(validatePositionName("x".repeat(POSITION_NAME_MAX_LENGTH + 1)).ok).toBe(false);
  });

  it("headcount: zero, vazio e negativo", () => {
    expect(parseHeadcountInput("0")).toEqual({ ok: true, value: 0 });
    expect(parseHeadcountInput("")).toEqual({ ok: true, value: null });
    expect(parseHeadcountInput("-1").ok).toBe(false);
    expect(parseHeadcountInput("1.5").ok).toBe(false);
  });

  it("duplicidade case/espaços", () => {
    const lines = [
      { localKey: "a", position_name: "Operador de Produção" },
      { localKey: "b", position_name: "Líder" },
    ];
    expect(findDuplicatePositionName(lines, "operador de produção", "x")).toBe(true);
    expect(findDuplicatePositionName(lines, " Operador de Produção ", "a")).toBe(false);
    expect(findDuplicatePositionName(lines, "Supervisor", "x")).toBe(false);
  });

  it("labels de autosave", () => {
    expect(personnelSaveStatusLabel("dirty")).toBe("Alterado");
    expect(personnelSaveStatusLabel("saving")).toBe("Salvando");
    expect(personnelSaveStatusLabel("saved")).toBe("Salvo");
    expect(personnelSaveStatusLabel("error")).toBe("Erro");
  });

  it("detecta conflito 409 de versão", () => {
    const err = new HttpRequestError(
      "[budget_personnel_line_version_conflict] conflito",
      409,
      { code: "budget_personnel_line_version_conflict" },
    );
    expect(isPersonnelVersionConflictError(err)).toBe(true);
    expect(mapPersonnelError(err)).toMatch(/budget_personnel_line_version_conflict/);
  });

  it("mapeia 401 e 403", () => {
    expect(mapPersonnelError(new HttpRequestError("x", 401))).toMatch(/401/);
    expect(mapPersonnelError(new HttpRequestError("x", 403))).toMatch(/403/);
  });

  it("labels e editabilidade do plano", () => {
    expect(personnelPlanStatusLabel("draft")).toBe("Rascunho");
    expect(personnelPlanStatusLabel("submitted")).toBe("Enviado para aprovação");
    expect(personnelPlanStatusLabel("changes_requested")).toBe("Ajustes solicitados");
    expect(personnelPlanStatusLabel("rejected")).toBe("Reprovado");
    expect(personnelPlanStatusLabel("approved")).toBe("Aprovado");
    expect(isPersonnelPlanEditable({ status: "draft" } as never)).toBe(true);
    expect(isPersonnelPlanEditable({ status: "submitted" } as never)).toBe(false);
    expect(canSubmitPersonnelPlanStatus({ status: "changes_requested" } as never)).toBe(
      true,
    );
  });

  it("conflito e segregação do plano", () => {
    const conflict = new HttpRequestError("x", 409, {
      code: "budget_personnel_plan_version_conflict",
    });
    expect(isPersonnelPlanVersionConflictError(conflict)).toBe(true);
    expect(
      mapPersonnelError(
        new HttpRequestError("x", 403, {
          code: "budget_personnel_approval_forbidden",
        }),
      ),
    ).toMatch(/segregação/i);
  });
});
