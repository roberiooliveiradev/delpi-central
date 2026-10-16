// @vitest-environment jsdom

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeMachineLoadOperation } from "../utils/machineLoadTestPayload";
import { machineLoadOperationKey } from "../utils/machineLoadOperationSelection";
import { useMachineLoadOperationSelection } from "./useMachineLoadOperationSelection";

const BRANCH = "01";
const BASE_SCOPE = `${BRANCH}|2026-02|2026-02|CT-01A|snapshot-1`;

const op = (overrides: Parameters<typeof makeMachineLoadOperation>[0] = {}) =>
  makeMachineLoadOperation(overrides);

const ROWS = [
  op({ production_order: "OP-A", operation_code: "01" }),
  op({ production_order: "OP-B", operation_code: "02" }),
  op({ production_order: "OP-C", operation_code: "03" }),
  op({ production_order: "OP-D", operation_code: "04" }),
  op({ production_order: "OP-E", operation_code: "05" }),
  op({ production_order: "OP-F", operation_code: "06" }),
  op({ production_order: "OP-G", operation_code: "07" }),
];

function renderSelection(rows = ROWS, scopeKey = BASE_SCOPE, visible = rows) {
  return renderHook(
    ({ r, v, s }) =>
      useMachineLoadOperationSelection({
        branch: BRANCH,
        scopeKey: s,
        rows: r,
        visibleRows: v,
      }),
    { initialProps: { r: rows, v: visible, s: scopeKey } },
  );
}

describe("useMachineLoadOperationSelection", () => {
  it("clique simples seleciona a operação e substitui seleção anterior", () => {
    const { result } = renderSelection();
    act(() => result.current.activate(ROWS[1]));
    expect(result.current.count).toBe(1);
    expect(result.current.isSelected(ROWS[1])).toBe(true);

    act(() => result.current.activate(ROWS[4]));
    expect(result.current.count).toBe(1);
    expect(result.current.isSelected(ROWS[4])).toBe(true);
    expect(result.current.isSelected(ROWS[1])).toBe(false);
  });

  it("Ctrl+clique alterna operações não consecutivas (B, E, G)", () => {
    const { result } = renderSelection();
    act(() => result.current.activate(ROWS[1]));
    act(() => result.current.activate(ROWS[4], { toggle: true }));
    act(() => result.current.activate(ROWS[6], { toggle: true }));
    expect(result.current.count).toBe(3);
    expect(
      result.current.selectedRows.map((row) => row.production_order),
    ).toEqual(["OP-B", "OP-E", "OP-G"]);

    // Ctrl+clique em item já selecionado remove.
    act(() => result.current.activate(ROWS[4], { toggle: true }));
    expect(result.current.count).toBe(2);
    expect(result.current.isSelected(ROWS[4])).toBe(false);
  });

  it("Shift+clique seleciona o intervalo contínuo na ordem visível", () => {
    const { result } = renderSelection();
    act(() => result.current.activate(ROWS[1])); // B = âncora
    act(() => result.current.activate(ROWS[5], { range: true })); // F
    expect(result.current.selectedRows.map((row) => row.production_order)).toEqual(
      ["OP-B", "OP-C", "OP-D", "OP-E", "OP-F"],
    );
  });

  it("Ctrl+Shift+clique adiciona o intervalo à seleção existente", () => {
    const { result } = renderSelection();
    act(() => result.current.activate(ROWS[0])); // A
    act(() => result.current.activate(ROWS[3], { toggle: true })); // D = nova âncora
    act(() => result.current.activate(ROWS[5], { toggle: true, range: true })); // D..F
    expect(result.current.selectedRows.map((row) => row.production_order)).toEqual(
      ["OP-A", "OP-D", "OP-E", "OP-F"],
    );
  });

  it("checkbox (toggle) compartilha o mesmo estado", () => {
    const { result } = renderSelection();
    act(() => result.current.toggle(ROWS[2]));
    expect(result.current.isSelected(ROWS[2])).toBe(true);
    act(() => result.current.toggle(ROWS[2]));
    expect(result.current.isSelected(ROWS[2])).toBe(false);
  });

  it("limpa seleção via clear e via mudança de escopo (CT)", () => {
    const { result, rerender } = renderSelection();
    act(() => result.current.activate(ROWS[1]));
    act(() => result.current.activate(ROWS[3], { toggle: true }));
    expect(result.current.count).toBe(2);

    act(() => result.current.clear());
    expect(result.current.count).toBe(0);

    act(() => result.current.activate(ROWS[1]));
    rerender({ r: ROWS, v: ROWS, s: `${BRANCH}|2026-02|2026-02|CT-02|snapshot-1` });
    expect(result.current.count).toBe(0);
  });

  it("trocar filtro (escopo) limpa a seleção", () => {
    const { result, rerender } = renderSelection();
    act(() => result.current.activate(ROWS[0]));
    rerender({ r: ROWS, v: ROWS, s: `${BASE_SCOPE}|hf` });
    expect(result.current.count).toBe(0);
  });

  it("operação removida da fila é podada da seleção", () => {
    const { result, rerender } = renderSelection();
    act(() => result.current.activate(ROWS[1]));
    act(() => result.current.activate(ROWS[2], { toggle: true }));
    expect(result.current.count).toBe(2);

    const remaining = ROWS.filter((row) => row !== ROWS[1]);
    rerender({ r: remaining, v: remaining, s: BASE_SCOPE });
    expect(result.current.count).toBe(1);
    expect(result.current.isSelected(ROWS[2])).toBe(true);
  });

  it("identidade inválida não é selecionável", () => {
    const invalid = op({ operation_code: "" });
    const { result } = renderSelection([...ROWS, invalid]);
    act(() => result.current.activate(invalid));
    expect(result.current.count).toBe(0);
    act(() => result.current.toggle(invalid));
    expect(result.current.count).toBe(0);
  });

  it("identidade duplicada no CT retorna 'ambiguous' e não escolhe arbitrariamente", () => {
    const dupA = op({ production_order: "DUP-1", operation_code: "01" });
    const dupB = op({ production_order: "DUP-1", operation_code: "01" });
    const rows = [ROWS[0], dupA, dupB];
    const { result } = renderSelection(rows);

    let outcome: string | null = null;
    act(() => {
      outcome = result.current.activate(dupB);
    });
    expect(outcome).toBe("ambiguous");
    expect(result.current.count).toBe(0);

    act(() => {
      outcome = result.current.toggle(dupA);
    });
    expect(outcome).toBe("ambiguous");
    expect(result.current.count).toBe(0);
  });

  it("visibleIndices acompanha a ordem visual atual", () => {
    const reversed = [...ROWS].reverse();
    const { result } = renderSelection(reversed);
    act(() => result.current.activate(reversed[2])); // OP-E agora no índice 2
    expect(result.current.visibleIndices).toEqual([2]);
  });

  it("Shift+clique usa a ordem VISÍVEL, não a fila completa", () => {
    // hideFinished escondeu C e D: intervalo B→E visível cobre só B e E.
    const visible = ROWS.filter(
      (row) => row.production_order !== "OP-C" && row.production_order !== "OP-D",
    );
    const { result } = renderSelection(ROWS, BASE_SCOPE, visible);
    act(() => result.current.activate(ROWS[1])); // B
    act(() => result.current.activate(ROWS[4], { range: true })); // E
    expect(result.current.selectedRows.map((row) => row.production_order)).toEqual(
      ["OP-B", "OP-E"],
    );
  });

  it("mesma OP+op em CTs diferentes não colide na chave canônica", () => {
    const otherCenter = op({ work_center: "CT-02", production_order: "OP-B", operation_code: "02" });
    const keyA = machineLoadOperationKey(ROWS[1], BRANCH);
    const keyB = machineLoadOperationKey(otherCenter, BRANCH);
    expect(keyA).not.toBe(keyB);
  });
});
