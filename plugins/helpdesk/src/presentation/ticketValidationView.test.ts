import { describe, expect, it } from "vitest";

import {
  approvalSummaryCounts,
  VALIDATION_STATUS_ACCEPTED,
  VALIDATION_STATUS_REFUSED,
  VALIDATION_STATUS_WAITING,
  validationStatusLabel,
} from "./ticketValidationView";

describe("ticketValidationView", () => {
  it("labels waiting/accepted/refused without inventing a global ticket status", () => {
    expect(validationStatusLabel(VALIDATION_STATUS_WAITING)).toBe("Aguardando decisão");
    expect(validationStatusLabel(VALIDATION_STATUS_ACCEPTED)).toBe("Aceita");
    expect(validationStatusLabel(VALIDATION_STATUS_REFUSED)).toBe("Recusada");
    expect(validationStatusLabel(99)).toBe("Status 99");
  });

  it("counts pending rows by waiting status only", () => {
    expect(approvalSummaryCounts(undefined)).toEqual({ total: 0, pending: 0 });
    expect(
      approvalSummaryCounts([
        { id: 1, status: VALIDATION_STATUS_WAITING },
        { id: 2, status: VALIDATION_STATUS_ACCEPTED },
        { id: 3, status: VALIDATION_STATUS_WAITING },
      ]),
    ).toEqual({ total: 3, pending: 2 });
  });
});
