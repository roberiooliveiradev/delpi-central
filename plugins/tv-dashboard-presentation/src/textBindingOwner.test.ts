import { describe, expect, it } from "vitest";

import {
  consolidateTextBindingToProjection,
  hasContradictoryTextBinding,
  readEffectiveTextProjection,
  resolveTextBindingOwner,
} from "./textBindingOwner";
import { resolveTextBlockDisplayRuns } from "./textViewProjection";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

describe("textBindingOwner", () => {
  const resolved: ComunicadoDataResolved = {
    kind: "kpi",
    label: "WEG SC",
    kpi: { value: 1_234_567.89, unit: "BRL" },
    contextValues: {
      "filter.start_date": "2025-01-01",
      "filter.end_date": "2025-09-24",
    },
    fields: [
      { name: "Rol", projectable: true, label: "Rol" },
      { name: "filter.start_date", projectable: true, label: "Início do filtro" },
      { name: "filter.end_date", projectable: true, label: "Fim do filtro" },
    ],
  };

  const dualBindBlock = {
    content: "ACUMULADO ",
    contentRuns: [
      { text: "ACUMULADO " },
      { text: "", dataRef: { field: "filter.start_date", format: "date" as const } },
      { text: " - " },
      { text: "", dataRef: { field: "filter.end_date", format: "date" as const } },
    ],
    textProjection: {
      field: "Rol",
      aggregation: "first" as const,
      prefix: "ACUMULADO ",
    },
    dataSourceId: "src-1",
  };

  it("resolveTextBindingOwner: dataRefs vencem textProjection", () => {
    expect(resolveTextBindingOwner(dualBindBlock)).toBe("contentRuns");
    expect(
      resolveTextBindingOwner({
        textProjection: { field: "Rol" },
      }),
    ).toBe("textProjection");
    expect(resolveTextBindingOwner({})).toBe("none");
  });

  it("readEffectiveTextProjection: lê owner do paint (primeiro dataRef), não Rol paralelo", () => {
    const effective = readEffectiveTextProjection(dualBindBlock);
    expect(effective.field).toBe("filter.start_date");
    expect(effective.prefix).toBe("ACUMULADO ");
  });

  it("P0: consolidar Campo=Rol remove dataRefs; paint usa Rol", () => {
    expect(hasContradictoryTextBinding(dualBindBlock)).toBe(true);
    const next = consolidateTextBindingToProjection(dualBindBlock, { field: "Rol" });
    expect(next.textProjection?.field).toBe("Rol");
    expect(next.textProjection?.prefix).toBe("ACUMULADO ");
    expect(next.contentRuns).toBeUndefined();
    expect(hasContradictoryTextBinding(next)).toBe(false);

    const painted = resolveTextBlockDisplayRuns(
      {
        content: next.content ?? "",
        contentRuns: next.contentRuns,
        textProjection: next.textProjection,
        dataSourceId: "src-1",
      },
      resolved,
    );
    const text = painted.map((r) => r.text).join("");
    expect(text).toContain("ACUMULADO");
    expect(text).not.toMatch(/01\/01\/2025/);
    expect(text).not.toMatch(/24\/09\/2025/);
  });

  it("sibling: só textProjection — patch preserva owner", () => {
    const block = {
      textProjection: { field: "Meta", aggregation: "first" as const, prefix: "X " },
    };
    const next = consolidateTextBindingToProjection(block, { field: "Rol" });
    expect(next.textProjection?.field).toBe("Rol");
    expect(next.textProjection?.prefix).toBe("X ");
    expect(resolveTextBindingOwner(next)).toBe("textProjection");
  });

  it("sibling: um dataRef — consolidar Campo troca o campo e limpa dataRef", () => {
    const block = {
      contentRuns: [{ text: "", dataRef: { field: "filter.start_date", format: "date" as const } }],
    };
    const next = consolidateTextBindingToProjection(block, { field: "Rol", aggregation: "first" });
    expect(next.textProjection?.field).toBe("Rol");
    expect(next.contentRuns).toBeUndefined();
  });

  it("negativo: sem escrever Campo, multi-run continua no paint", () => {
    expect(resolveTextBindingOwner(dualBindBlock)).toBe("contentRuns");
    const painted = resolveTextBlockDisplayRuns(dualBindBlock, resolved);
    const text = painted.map((r) => r.text).join("");
    expect(text).toMatch(/01\/01\/2025/);
    expect(text).toMatch(/24\/09\/2025/);
  });
});
