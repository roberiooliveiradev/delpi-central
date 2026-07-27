import { describe, expect, it } from "vitest";
import {
  LIST_STATUS_FILTER_OPEN,
  STATUS_FILTER_OPTIONS,
  statusTone,
} from "./status";

describe("statusTone", () => {
  it("mapeia status para o tom visual da fila/badge", () => {
    expect(statusTone("pending")).toBe("pending");
    expect(statusTone("in_progress")).toBe("progress");
    expect(statusTone("blocked")).toBe("blocked");
    expect(statusTone("posted")).toBe("posted");
    expect(statusTone("cancelled")).toBe("cancelled");
  });

  it("usa pending como fallback", () => {
    expect(statusTone("unknown")).toBe("pending");
  });
});

describe("STATUS_FILTER_OPTIONS", () => {
  it("oferece filtro open como fila em aberto", () => {
    expect(STATUS_FILTER_OPTIONS[0]?.value).toBe(LIST_STATUS_FILTER_OPEN);
    expect(STATUS_FILTER_OPTIONS.some((o) => o.value === "pending")).toBe(true);
  });
});
