import { describe, expect, it } from "vitest";

import { makeMachineLoadPayload } from "./machineLoadTestPayload";
import { resolveSelectedWorkCenter, selectMachineLoadCenter } from "./machineLoadSelection";

describe("selectMachineLoadCenter", () => {
  it("recorta o centro pedido a partir da fila que já está em memória", () => {
    const payload = makeMachineLoadPayload();

    const first = selectMachineLoadCenter(payload, "CT-01A");
    const second = selectMachineLoadCenter(payload, "CT-02");

    expect(first.selected.work_center).toBe("CT-01A");
    expect(first.selected.items.map((item) => item.production_order)).toEqual([
      "24640401002",
      "24640401003",
    ]);
    expect(second.selected.work_center).toBe("CT-02");
    expect(second.selected.items.map((item) => item.production_order)).toEqual(["24640401010"]);
  });

  it("nunca devolve fila vazia para um centro que tem operações", () => {
    const payload = makeMachineLoadPayload();

    for (const center of payload.work_centers) {
      const scoped = selectMachineLoadCenter(payload, center.work_center);
      expect(scoped.selected.items.length).toBe(center.operation_count);
    }
  });

  it("centro desconhecido cai na primeira aba, igual à API", () => {
    const payload = makeMachineLoadPayload();

    const scoped = selectMachineLoadCenter(payload, "CT-ZZZ");

    expect(scoped.selected.work_center).toBe("CT-01A");
    expect(scoped.selected.requested_work_center).toBe("CT-ZZZ");
    expect(scoped.selected.items).toHaveLength(2);
  });

  it("sem a fila completa preserva o recorte que a API mandou", () => {
    const complete = makeMachineLoadPayload();
    const payload = makeMachineLoadPayload({
      operations: undefined,
      selected: { ...complete.selected, work_center: "CT-02" },
    });

    const scoped = selectMachineLoadCenter(payload, "CT-01A");

    expect(scoped).toBe(payload);
    expect(scoped.selected.work_center).toBe("CT-02");
  });
});

describe("resolveSelectedWorkCenter", () => {
  it("ignora espaços em volta do código do centro", () => {
    const centers = [{ work_center: " CT-02 " }];
    expect(resolveSelectedWorkCenter(centers, "CT-02")).toBe("CT-02");
  });

  it("sem centro nenhum não há aba para selecionar", () => {
    expect(resolveSelectedWorkCenter([], "CT-02")).toBeNull();
  });
});
