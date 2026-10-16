import { describe, expect, it } from "vitest";

import { makeMachineLoadOperation } from "./machineLoadTestPayload";
import {
  groupSelectedMachineLoadOperations,
  machineLoadOperationHasOpenRun,
} from "./machineLoadGrouping";
import { machineLoadOperationKey } from "./machineLoadOperationSelection";

const op = (id: string, overrides: Parameters<typeof makeMachineLoadOperation>[0] = {}) =>
  makeMachineLoadOperation({ production_order: `OP-${id}`, operation_code: "01", ...overrides });

const keysOf = (rows: Array<{ production_order: string; operation_code: string }>) =>
  rows.map((row) => `${row.production_order}`);

const select = (...rows: ReturnType<typeof op>[]) =>
  new Set(rows.map((row) => machineLoadOperationKey(row)!));

const QUEUE = ["A", "B", "C", "D", "E", "F", "G"].map((id, index) =>
  op(id, { operation_code: `0${index + 1}` }),
);

describe("machineLoadOperationHasOpenRun", () => {
  it("protege producing/stopped/paused/unknown e inconsistente", () => {
    for (const status of ["producing", "stopped", "paused", "unknown"] as const) {
      expect(machineLoadOperationHasOpenRun(op("X", { execution_status: status }))).toBe(true);
    }
    expect(
      machineLoadOperationHasOpenRun(
        op("X", { execution_integrity_status: "inconsistent" }),
      ),
    ).toBe(true);
    expect(machineLoadOperationHasOpenRun(op("X"))).toBe(false);
  });
});

describe("groupSelectedMachineLoadOperations", () => {
  it("caso canônico: B,E,G viram consecutivas na posição de B", () => {
    const outcome = groupSelectedMachineLoadOperations(
      QUEUE,
      select(QUEUE[1], QUEUE[4], QUEUE[6]),
    );
    expect(outcome.status).toBe("ok");
    if (outcome.status !== "ok") return;
    expect(keysOf(outcome.nextRows)).toEqual([
      "OP-A",
      "OP-B",
      "OP-E",
      "OP-G",
      "OP-C",
      "OP-D",
      "OP-F",
    ]);
    expect(outcome.groupedCount).toBe(3);
  });

  it("âncora é a primeira selecionada NA FILA — ordem dos cliques não importa", () => {
    // Set montado «clicando» primeiro em G, depois E, depois B.
    const outcome = groupSelectedMachineLoadOperations(
      QUEUE,
      select(QUEUE[6], QUEUE[4], QUEUE[1]),
    );
    expect(outcome.status).toBe("ok");
    if (outcome.status !== "ok") return;
    expect(keysOf(outcome.nextRows).slice(0, 4)).toEqual(["OP-A", "OP-B", "OP-E", "OP-G"]);
  });

  it("ordem relativa de selecionadas e não selecionadas é preservada", () => {
    const outcome = groupSelectedMachineLoadOperations(QUEUE, select(QUEUE[5], QUEUE[2]));
    expect(outcome.status).toBe("ok");
    if (outcome.status !== "ok") return;
    // Âncora = C (índice 2): A B [C F] D E G
    expect(keysOf(outcome.nextRows)).toEqual([
      "OP-A",
      "OP-B",
      "OP-C",
      "OP-F",
      "OP-D",
      "OP-E",
      "OP-G",
    ]);
  });

  it("não perde nem duplica operações — permutação exata", () => {
    const outcome = groupSelectedMachineLoadOperations(
      QUEUE,
      select(QUEUE[0], QUEUE[3], QUEUE[6]),
    );
    expect(outcome.status).toBe("ok");
    if (outcome.status !== "ok") return;
    expect(outcome.nextRows.length).toBe(QUEUE.length);
    expect(new Set(outcome.nextRows.map((r) => machineLoadOperationKey(r))).size).toBe(
      QUEUE.length,
    );
    expect(outcome.nextRows[0]).toBe(QUEUE[0]);
    expect(keysOf(outcome.nextRows).slice(0, 3)).toEqual(["OP-A", "OP-D", "OP-G"]);
  });

  it("seleção já contígua é noop — não gera write", () => {
    const outcome = groupSelectedMachineLoadOperations(
      QUEUE,
      select(QUEUE[2], QUEUE[3], QUEUE[4]),
    );
    expect(outcome.status).toBe("noop");
  });

  it("menos de duas selecionadas não agrupa", () => {
    expect(groupSelectedMachineLoadOperations(QUEUE, select(QUEUE[1])).status).toBe(
      "too_few",
    );
    expect(groupSelectedMachineLoadOperations(QUEUE, new Set()).status).toBe("too_few");
  });

  it("run aberto deslocado pelo bloco bloqueia o agrupamento", () => {
    const rows = [...QUEUE];
    rows[3] = op("D", { operation_code: "04", execution_status: "producing" });
    const outcome = groupSelectedMachineLoadOperations(
      rows,
      select(rows[1], rows[5]),
    );
    expect(outcome.status).toBe("protected");
    if (outcome.status !== "protected") return;
    expect(outcome.blocked.production_order).toBe("OP-D");
  });

  it("run aberto na PRÓPRIA âncora não bloqueia — a posição não muda", () => {
    const rows = [...QUEUE];
    rows[1] = op("B", { operation_code: "02", execution_status: "stopped" });
    const outcome = groupSelectedMachineLoadOperations(rows, select(rows[1], rows[4]));
    expect(outcome.status).toBe("ok");
    if (outcome.status !== "ok") return;
    expect(outcome.nextRows.indexOf(rows[1])).toBe(1);
  });

  it("run aberto em operação selecionada fora da âncora bloqueia", () => {
    const rows = [...QUEUE];
    rows[4] = op("E", { operation_code: "05", execution_status: "unknown" });
    const outcome = groupSelectedMachineLoadOperations(
      rows,
      select(rows[1], rows[4]),
    );
    expect(outcome.status).toBe("protected");
  });

  it("run aberto FORA do intervalo afetado não bloqueia", () => {
    const rows = [...QUEUE];
    rows[6] = op("G", { operation_code: "07", execution_status: "paused" });
    const outcome = groupSelectedMachineLoadOperations(rows, select(rows[1], rows[3]));
    expect(outcome.status).toBe("ok");
  });

  it("chave selecionada duplicada na fila falha com segurança", () => {
    const dup = op("B", { operation_code: "02" });
    const rows = [QUEUE[0], QUEUE[1], dup, ...QUEUE.slice(2)];
    const outcome = groupSelectedMachineLoadOperations(
      rows,
      select(QUEUE[1], QUEUE[4]),
    );
    expect(outcome.status).toBe("ambiguous");
  });

  it("não muta a fila original", () => {
    const rows = [...QUEUE];
    const snapshot = [...rows];
    groupSelectedMachineLoadOperations(rows, select(rows[1], rows[4]));
    expect(rows).toEqual(snapshot);
  });
});
