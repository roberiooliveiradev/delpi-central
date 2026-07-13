import { describe, expect, it } from "vitest";

import {
  applyValueFieldSelectionToBinding,
  patchValueFieldSelection,
  resolveCheckedValueFields,
} from "./ValueFieldsMultiSelect";

const options = [
  { field: "total_lmps", label: "Total" },
  { field: "avg_lead_time", label: "Lead" },
];

describe("ValueFieldsMultiSelect helpers", () => {
  it("marca todas quando não há seleção", () => {
    expect([...resolveCheckedValueFields(options)]).toEqual(["total_lmps", "avg_lead_time"]);
  });

  it("desmarcar um produz selectedValueFields; desmarcar o último volta ao automático", () => {
    const onlyOne = patchValueFieldSelection(
      options,
      new Set(["total_lmps", "avg_lead_time"]),
      "avg_lead_time",
      false,
    );
    expect(onlyOne.selectedValueFields).toEqual(["total_lmps"]);

    const none = patchValueFieldSelection(
      options,
      new Set(["total_lmps"]),
      "total_lmps",
      false,
    );
    expect(none.selectedValueFields).toBeUndefined();
  });

  it("applyValueFieldSelectionToBinding limpa campos no automático", () => {
    const next = applyValueFieldSelectionToBinding(
      {
        operationId: "get_lmps_dashboard_summary",
        selectedValueFields: ["total_lmps"],
        valueField: "total_lmps",
      },
      {},
    );
    expect(next.selectedValueFields).toBeUndefined();
    expect(next.valueField).toBeUndefined();
  });
});
