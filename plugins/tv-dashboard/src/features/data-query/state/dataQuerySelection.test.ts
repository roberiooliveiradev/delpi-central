import { describe, expect, it } from "vitest";

import type { DataQueryCompiledStep } from "../domain/dataQueryTypes";
import { resolveStepAfterMutation } from "./dataQuerySelection";

function step(name: string, formula: string): DataQueryCompiledStep {
  return { name, label: name, operation: "Table.Sort", formula };
}

describe("resolveStepAfterMutation", () => {
  it("foca a etapa recém-inserida", () => {
    const previous = [step("Renomeadas", "Table.RenameColumns(Fonte, ...)")];
    const next = [
      ...previous,
      step("Linhas ordenadas", 'Table.Sort(Renomeadas, {{"a", Order.Ascending}})'),
    ];
    expect(
      resolveStepAfterMutation(
        {
          type: "insert_step",
          afterStepName: "Renomeadas",
          operation: "sort",
          arguments: {},
        },
        "Renomeadas",
        previous,
        next,
      ),
    ).toBe("Linhas ordenadas");
  });

  it("foca a etapa coalescida quando o sort adjacente é substituído", () => {
    const previous = [
      step("Renomeadas", "Table.RenameColumns(Fonte, ...)"),
      step("Linhas ordenadas", 'Table.Sort(Renomeadas, {{"a", Order.Ascending}})'),
    ];
    const next = [
      previous[0]!,
      step("Linhas ordenadas", 'Table.Sort(Renomeadas, {{"a", Order.Descending}})'),
    ];
    expect(
      resolveStepAfterMutation(
        {
          type: "insert_step",
          afterStepName: "Renomeadas",
          operation: "sort",
          arguments: {},
        },
        "Renomeadas",
        previous,
        next,
      ),
    ).toBe("Linhas ordenadas");
  });

  it("mantém a seleção nas demais mutações", () => {
    const steps = [step("Renomeadas", "Table.RenameColumns(Fonte, ...)")];
    expect(
      resolveStepAfterMutation(
        { type: "format_script" },
        "Renomeadas",
        steps,
        steps,
      ),
    ).toBe("Renomeadas");
  });
});
