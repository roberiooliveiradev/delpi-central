import { describe, expect, it } from "vitest";

import {
  canConnectBlocks,
  createConnectorBlock,
  isConnectorShapeBlock,
  normalizeShapeConnector,
  parseComunicadoConfig,
  pruneOrphanConnectors,
  reconcileConnectorsAfterDrag,
  serializeComunicadoConfig,
  syncAllConnectors,
  type ComunicadoBlock,
} from "./index";

function rect(id: string, x: number, y: number, w = 10, h = 10): ComunicadoBlock {
  return {
    id,
    type: "shape",
    shape: "rectangle",
    frame: { x, y, w, h },
    style: { zIndex: 1 },
  };
}

describe("comunicadoConnectors", () => {
  it("normalizeShapeConnector rejeita ids iguais ou vazios", () => {
    expect(normalizeShapeConnector({ fromBlockId: "a", toBlockId: "a" })).toBeUndefined();
    expect(normalizeShapeConnector({ fromBlockId: "", toBlockId: "b" })).toBeUndefined();
    expect(normalizeShapeConnector({ fromBlockId: "a", toBlockId: "b", fromAnchor: "n" })).toEqual({
      fromBlockId: "a",
      toBlockId: "b",
      fromAnchor: "n",
      toAnchor: "center",
    });
  });

  it("createConnectorBlock liga centros e gera vertices", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 40, 20, 10);
    const line = createConnectorBlock(a, b);
    expect(isConnectorShapeBlock(line)).toBe(true);
    expect(line.connector?.fromBlockId).toBe("a");
    expect(line.connector?.toBlockId).toBe("b");
    expect(line.vertices).toEqual([
      { x: 10, y: 5 },
      { x: 90, y: 45 },
    ]);
    expect(canConnectBlocks(a, b)).toBe(true);
    expect(canConnectBlocks(a, line)).toBe(false);
  });

  it("syncAllConnectors atualiza endpoints quando o alvo se move", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 40, 20, 10);
    const line = createConnectorBlock(a, b);
    const movedB = { ...b, frame: { ...b.frame, x: 60, y: 20 } };
    const synced = syncAllConnectors([a, movedB, line]);
    const nextLine = synced.find((block) => block.id === line.id);
    expect(nextLine && isConnectorShapeBlock(nextLine) ? nextLine.vertices : null).toEqual([
      { x: 10, y: 5 },
      { x: 70, y: 25 },
    ]);
  });

  it("reconcileConnectorsAfterDrag solta o conector arrastado e mantém os demais", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 40, 20, 10);
    const line = createConnectorBlock(a, b);
    const dragged = {
      ...line,
      frame: { x: 30, y: 30, w: 20, h: 5 },
    };
    const next = reconcileConnectorsAfterDrag([a, b, dragged], new Set([line.id]));
    const free = next.find((block) => block.id === line.id);
    expect(free && free.type === "shape" ? free.connector : "missing").toBeUndefined();
  });

  it("pruneOrphanConnectors remove linha sem alvo", () => {
    const a = rect("a", 0, 0);
    const b = rect("b", 50, 50);
    const line = createConnectorBlock(a, b);
    expect(pruneOrphanConnectors([a, line]).map((block) => block.id)).toEqual(["a"]);
  });

  it("parse/serialize preserva connector e vertices", () => {
    const a = rect("a", 0, 0, 20, 10);
    const b = rect("b", 80, 40, 20, 10);
    const line = createConnectorBlock(a, b);
    const config = parseComunicadoConfig({
      version: 3,
      blocks: [a, b, line],
    });
    const serialized = serializeComunicadoConfig(config);
    const reloaded = parseComunicadoConfig(serialized as Record<string, unknown>);
    const reloadedLine = reloaded.blocks.find((block) => block.id === line.id);
    expect(reloadedLine && isConnectorShapeBlock(reloadedLine)).toBe(true);
    expect(reloadedLine && reloadedLine.type === "shape" ? reloadedLine.vertices : null).toEqual(
      line.vertices,
    );
  });
});
