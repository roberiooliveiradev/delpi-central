import { describe, expect, it } from "vitest";

import { makeMachineLoadOperation } from "./machineLoadTestPayload";
import {
  addKeysToSelection,
  duplicatedOperationKeys,
  machineLoadOperationKey,
  machineLoadSelectionScopeKey,
  rangeOperationKeys,
  resolveSelectedOperations,
  selectedVisibleIndices,
  toggleKeyInSelection,
} from "./machineLoadOperationSelection";

const op = (overrides: Parameters<typeof makeMachineLoadOperation>[0] = {}) =>
  makeMachineLoadOperation(overrides);

describe("machineLoadOperationKey", () => {
  it("monta a identidade canônica filial+CT+OP+operação", () => {
    const key = machineLoadOperationKey(
      op({ work_center: "CT-01A", production_order: "24640401002", operation_code: "03" }),
    );
    expect(JSON.parse(key!)).toEqual(["01", "CT-01A", "24640401002", "03"]);
  });

  it("a mesma OP+operação em CTs diferentes gera chaves diferentes", () => {
    const a = machineLoadOperationKey(op({ work_center: "CT-01A" }));
    const b = machineLoadOperationKey(op({ work_center: "CT-02" }));
    expect(a).not.toBe(b);
  });

  it("preserva zeros à esquerda e não usa concatenação ambígua", () => {
    const key = machineLoadOperationKey(
      op({ production_order: "00770001001", operation_code: "005" }),
    )!;
    expect(JSON.parse(key)[2]).toBe("00770001001");
    expect(JSON.parse(key)[3]).toBe("005");
    // Tupla serializada não confunde campos que contenham o separador visual.
    const tricky = machineLoadOperationKey(
      op({ work_center: 'CT-"x"', production_order: "24640401002" }),
    )!;
    expect(JSON.parse(tricky)[1]).toBe('CT-"x"');
  });

  it("retorna null quando falta parte da identidade", () => {
    expect(machineLoadOperationKey(op({ work_center: "" }))).toBeNull();
    expect(machineLoadOperationKey(op({ production_order: "" }))).toBeNull();
    expect(machineLoadOperationKey(op({ operation_code: "" }))).toBeNull();
    expect(
      machineLoadOperationKey({ ...op(), branch: "" }),
    ).toBeNull();
  });

  it("usa a filial de fallback quando a linha não traz branch", () => {
    const row = { ...op(), branch: "" };
    expect(machineLoadOperationKey(row, "02")).toBe(
      JSON.stringify(["02", "CT-01A", "24640401002", "03"]),
    );
  });
});

describe("duplicatedOperationKeys", () => {
  it("detecta a mesma identidade canônica duplicada dentro do CT", () => {
    const rows = [
      op({ work_center: "CT-01A", production_order: "24640401002" }),
      op({ work_center: "CT-01A", production_order: "24640401002" }),
      op({ work_center: "CT-01A", production_order: "24640401003" }),
    ];
    const dup = duplicatedOperationKeys(rows);
    expect(dup.size).toBe(1);
    expect([...dup][0]).toBe(machineLoadOperationKey(rows[0]));
  });

  it("a mesma OP+op em CTs distintos NÃO é duplicata", () => {
    const rows = [
      op({ work_center: "CT-01A", production_order: "24640401002" }),
      op({ work_center: "CT-02", production_order: "24640401002" }),
    ];
    expect(duplicatedOperationKeys(rows).size).toBe(0);
  });
});

describe("rangeOperationKeys", () => {
  const visible = ["A", "B", "C", "D", "E", "F", "G"];

  it("seleciona o intervalo contínuo na ordem visível", () => {
    expect(rangeOperationKeys(visible, "B", "F")).toEqual(["B", "C", "D", "E", "F"]);
  });

  it("funciona em ordem inversa (alvo acima da âncora)", () => {
    expect(rangeOperationKeys(visible, "F", "B")).toEqual(["B", "C", "D", "E", "F"]);
  });

  it("devolve vazio quando a âncora não está visível", () => {
    expect(rangeOperationKeys(visible, "Z", "B")).toEqual([]);
  });
});

describe("toggleKeyInSelection / addKeysToSelection", () => {
  it("adiciona e remove alternadamente", () => {
    let sel = new Set<string>();
    sel = toggleKeyInSelection(sel, "B");
    sel = toggleKeyInSelection(sel, "E");
    sel = toggleKeyInSelection(sel, "G");
    expect([...sel]).toEqual(["B", "E", "G"]);
    sel = toggleKeyInSelection(sel, "E");
    expect([...sel]).toEqual(["B", "G"]);
  });

  it("adiciona intervalo à seleção existente sem duplicar", () => {
    const sel = addKeysToSelection(new Set(["A"]), ["A", "B", "C"]);
    expect([...sel].sort()).toEqual(["A", "B", "C"]);
  });
});

describe("machineLoadSelectionScopeKey", () => {
  const base = {
    branch: "01",
    startDate: "2026-02-01",
    endDate: "2026-02-28",
    workCenter: "CT-01A",
    refreshedAt: "2026-02-10T10:00:00Z",
    sequenceUpdatedAt: "2026-02-10T11:00:00Z",
  };

  it("é determinístico para o mesmo contexto", () => {
    expect(machineLoadSelectionScopeKey(base)).toBe(
      machineLoadSelectionScopeKey({ ...base }),
    );
  });

  it("muda quando a filial, o CT, o período ou os filtros mudam", () => {
    const key = machineLoadSelectionScopeKey(base);
    expect(machineLoadSelectionScopeKey({ ...base, branch: "02" })).not.toBe(key);
    expect(machineLoadSelectionScopeKey({ ...base, workCenter: "CT-02" })).not.toBe(key);
    expect(machineLoadSelectionScopeKey({ ...base, startDate: "2026-03-01" })).not.toBe(key);
    expect(machineLoadSelectionScopeKey({ ...base, endDate: "2026-03-31" })).not.toBe(key);
    expect(machineLoadSelectionScopeKey({ ...base, hideFinished: true })).not.toBe(key);
    expect(machineLoadSelectionScopeKey({ ...base, feedbackOnly: true })).not.toBe(key);
  });

  it("muda quando o snapshot é regenerado (refreshed_at)", () => {
    expect(
      machineLoadSelectionScopeKey({ ...base, refreshedAt: "2026-02-10T12:00:00Z" }),
    ).not.toBe(machineLoadSelectionScopeKey(base));
  });

  it("muda quando a sequência persiste mutação com o MESMO refreshed_at", () => {
    // Reordenação/priorização/otimização/transferência bumpam
    // sequence_updated_at sem tocar refreshed_at — a seleção não pode
    // sobreviver a uma fila que já não corresponde ao contexto visual.
    expect(
      machineLoadSelectionScopeKey({
        ...base,
        sequenceUpdatedAt: "2026-02-10T12:30:00Z",
      }),
    ).not.toBe(machineLoadSelectionScopeKey(base));
  });

  it("não confunde campos com separador — tupla serializada, não join", () => {
    const a = machineLoadSelectionScopeKey({ ...base, workCenter: 'CT|"x"' });
    const b = machineLoadSelectionScopeKey({ ...base, workCenter: "CT", branch: '"x"' });
    expect(a).not.toBe(b);
  });
});

describe("resolveSelectedOperations / selectedVisibleIndices", () => {
  const rows = [
    op({ production_order: "A1", operation_code: "01" }),
    op({ production_order: "B1", operation_code: "02" }),
    op({ production_order: "C1", operation_code: "03" }),
  ];
  const keys = rows.map((row) => machineLoadOperationKey(row)!);

  it("devolve as operações na ordem da fila, não da seleção", () => {
    const result = resolveSelectedOperations(rows, new Set([keys[2], keys[0]]));
    expect(result.map((r) => r.production_order)).toEqual(["A1", "C1"]);
  });

  it("chave de operação fora da fila não produz linha nem índice", () => {
    const stale = new Set([keys[1], JSON.stringify(["01", "CT-02", "X9", "09"])]);
    expect(resolveSelectedOperations(rows, stale).map((r) => r.production_order)).toEqual(["B1"]);
    expect(selectedVisibleIndices(rows, stale)).toEqual([1]);
  });
});
