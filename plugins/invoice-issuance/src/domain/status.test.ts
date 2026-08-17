import { describe, expect, it } from "vitest";
import { hasAction, historyEventLabel, invoiceTypeLabel, statusLabel, statusTone } from "./status";

describe("status helpers", () => {
  it("rótula estados da fila", () => {
    expect(statusLabel("pending")).toContain("Aguardando");
    expect(statusTone("issued")).toBe("posted");
    expect(statusTone("returned")).toBe("blocked");
  });

  it("rótula tipo de NF", () => {
    expect(invoiceTypeLabel("sale")).toBe("Venda");
    expect(invoiceTypeLabel("repair_shipment")).toContain("conserto");
  });

  it("detecta ação permitida", () => {
    expect(hasAction(["start", "issue"], "start")).toBe(true);
    expect(hasAction(["start"], "cancel")).toBe(false);
  });

  it("rótula eventos do histórico em português", () => {
    expect(historyEventLabel("created")).toBe("Solicitação criada");
    expect(historyEventLabel("updated")).toBe("Dados atualizados");
    expect(historyEventLabel("resubmitted")).toBe("Reenviada");
    expect(historyEventLabel("started")).toBe("Atendimento iniciado");
    expect(historyEventLabel("returned")).toBe("Devolvida");
    expect(historyEventLabel("issued")).toBe("Emitida");
    expect(historyEventLabel("cancelled")).toBe("Cancelada");
  });
});
