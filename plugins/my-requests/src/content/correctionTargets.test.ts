import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  correctionTargetOptionsForType,
  wizardStepIdsForCorrectionTargets,
} from "./correctionTargets";

describe("correctionTargets catalog", () => {
  it("expõe seções de NF alinhadas ao wizard", () => {
    const opts = correctionTargetOptionsForType("invoice-issuance");
    expect(opts.map((row) => row.id)).toEqual([
      "recipient",
      "invoice_type",
      "items",
      "freight",
      "extras",
    ]);
    expect(wizardStepIdsForCorrectionTargets(["invoice_type", "items"])).toEqual([
      "invoiceType",
      "items",
    ]);
  });

  it("modal de devolução marca campos e detalhe exibe targets", () => {
    const root = join(dirname(fileURLToPath(import.meta.url)), "..");
    const modal = readFileSync(join(root, "components/ReasonConfirmModal.tsx"), "utf8");
    const detail = readFileSync(join(root, "pages/RequestDetailPage.tsx"), "utf8");
    const api = readFileSync(join(root, "api/requestsApi.ts"), "utf8");
    expect(modal).toMatch(/Campos a corrigir/);
    expect(modal).toMatch(/NativeCheckboxControl/);
    expect(modal).toMatch(/correctionTargets/);
    expect(detail).toMatch(/correctionTargetOptionsForType/);
    expect(detail).toMatch(/correction_targets/);
    expect(api).toMatch(/correction_targets/);
  });
});
