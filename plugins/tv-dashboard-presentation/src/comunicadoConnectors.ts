/**
 * Conectores entre blocos — linha reta ligada a âncoras (MVP PPT).
 * Endpoints vivem em `vertices` + `frame` derivados; `connector` guarda a ligação.
 */

import type {
  ComunicadoBlock,
  ComunicadoFrame,
  ComunicadoGeometryVertex,
  ComunicadoShapeBlock,
  ComunicadoShapeConnector,
} from "./comunicadoTypes";
import { geometryBoundingFrame } from "./comunicadoShapeGeometry";
import { isLineShapeKind } from "./comunicadoVisualPrimitive";

export type ComunicadoConnectorAnchor = NonNullable<ComunicadoShapeConnector["fromAnchor"]>;

export type { ComunicadoShapeConnector };

const ANCHORS = new Set<ComunicadoConnectorAnchor>(["center", "n", "s", "e", "w"]);

function newConnectorId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `conn-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function normalizeConnectorAnchor(value: unknown): ComunicadoConnectorAnchor {
  if (typeof value === "string" && ANCHORS.has(value as ComunicadoConnectorAnchor)) {
    return value as ComunicadoConnectorAnchor;
  }
  return "center";
}

export function normalizeShapeConnector(value: unknown): ComunicadoShapeConnector | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const fromBlockId = typeof raw.fromBlockId === "string" ? raw.fromBlockId.trim() : "";
  const toBlockId = typeof raw.toBlockId === "string" ? raw.toBlockId.trim() : "";
  if (!fromBlockId || !toBlockId || fromBlockId === toBlockId) return undefined;
  return {
    fromBlockId,
    toBlockId,
    fromAnchor: normalizeConnectorAnchor(raw.fromAnchor),
    toAnchor: normalizeConnectorAnchor(raw.toAnchor),
  };
}

export function isConnectorShapeBlock(
  block: ComunicadoBlock | null | undefined,
): block is ComunicadoShapeBlock & { connector: ComunicadoShapeConnector } {
  return Boolean(
    block &&
      block.type === "shape" &&
      isLineShapeKind(block.shape) &&
      block.connector &&
      block.connector.fromBlockId &&
      block.connector.toBlockId,
  );
}

/** Ponto de âncora (% do palco) a partir do frame do bloco. */
export function resolveBlockAnchorPoint(
  block: ComunicadoBlock,
  anchor: ComunicadoConnectorAnchor = "center",
): ComunicadoGeometryVertex {
  const { x, y, w, h } = block.frame;
  switch (anchor) {
    case "n":
      return { x: x + w / 2, y };
    case "s":
      return { x: x + w / 2, y: y + h };
    case "w":
      return { x, y: y + h / 2 };
    case "e":
      return { x: x + w, y: y + h / 2 };
    case "center":
    default:
      return { x: x + w / 2, y: y + h / 2 };
  }
}

export function resolveConnectorEndpoints(
  blocks: ComunicadoBlock[],
  connector: ComunicadoShapeConnector,
): [ComunicadoGeometryVertex, ComunicadoGeometryVertex] | null {
  const from = blocks.find((block) => block.id === connector.fromBlockId);
  const to = blocks.find((block) => block.id === connector.toBlockId);
  if (!from || !to) return null;
  return [
    resolveBlockAnchorPoint(from, normalizeConnectorAnchor(connector.fromAnchor)),
    resolveBlockAnchorPoint(to, normalizeConnectorAnchor(connector.toAnchor)),
  ];
}

function frameFromLinePoints(points: ComunicadoGeometryVertex[]): ComunicadoFrame {
  return geometryBoundingFrame({ primitive: "line", points });
}

/** Atualiza vertices + frame de um bloco conector a partir dos alvos atuais. */
export function applyConnectorGeometry(
  lineBlock: ComunicadoShapeBlock,
  blocks: ComunicadoBlock[],
): ComunicadoShapeBlock {
  const connector = lineBlock.connector;
  if (!connector) return lineBlock;
  const endpoints = resolveConnectorEndpoints(blocks, connector);
  if (!endpoints) {
    const { connector: _drop, ...rest } = lineBlock;
    return rest as ComunicadoShapeBlock;
  }
  const [a, b] = endpoints;
  const vertices = [a, b];
  return {
    ...lineBlock,
    connector,
    vertices,
    frame: frameFromLinePoints(vertices),
  };
}

/** Recalcula todos os conectores após mover/redimensionar blocos. */
export function syncAllConnectors(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  const hasConnector = blocks.some((block) => isConnectorShapeBlock(block));
  if (!hasConnector) return blocks;
  return blocks.map((block) => {
    if (!isConnectorShapeBlock(block)) return block;
    return applyConnectorGeometry(block, blocks);
  });
}

export function canConnectBlocks(a: ComunicadoBlock, b: ComunicadoBlock): boolean {
  if (a.id === b.id) return false;
  if (isConnectorShapeBlock(a) || isConnectorShapeBlock(b)) return false;
  return true;
}

export function createConnectorBlock(
  from: ComunicadoBlock,
  to: ComunicadoBlock,
  options?: {
    shape?: "line" | "line-arrow-right" | "line-arrow-left" | "line-arrow-both";
    zIndex?: number;
  },
): ComunicadoShapeBlock {
  const shape = options?.shape ?? "line-arrow-right";
  const connector: ComunicadoShapeConnector = {
    fromBlockId: from.id,
    toBlockId: to.id,
    fromAnchor: "center",
    toAnchor: "center",
  };
  const draft: ComunicadoShapeBlock = {
    id: newConnectorId(),
    type: "shape",
    shape,
    frame: { x: 0, y: 0, w: 10, h: 4 },
    style: {
      zIndex: options?.zIndex ?? 2,
      stroke: "#64748b",
      strokeWidth: 2,
      fill: "transparent",
    },
    connector,
    content: "",
  };
  return applyConnectorGeometry(draft, [from, to, draft]);
}

/** Remove ligação se o conector for editado manualmente (move/resize próprio). */
export function detachConnector(block: ComunicadoShapeBlock): ComunicadoShapeBlock {
  if (!block.connector) return block;
  const { connector: _drop, ...rest } = block;
  return rest as ComunicadoShapeBlock;
}

export function connectorsReferencingBlock(
  blocks: ComunicadoBlock[],
  blockId: string,
): ComunicadoShapeBlock[] {
  return blocks.filter(
    (block): block is ComunicadoShapeBlock =>
      isConnectorShapeBlock(block) &&
      (block.connector.fromBlockId === blockId || block.connector.toBlockId === blockId),
  );
}

/** Após apagar blocos: remove conectores órfãos (sem um dos alvos). */
export function pruneOrphanConnectors(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  const ids = new Set(blocks.map((block) => block.id));
  return blocks.filter((block) => {
    if (!isConnectorShapeBlock(block)) return true;
    return ids.has(block.connector.fromBlockId) && ids.has(block.connector.toBlockId);
  });
}

/**
 * Após mover/redimensionar: desliga conectores arrastados e sincroniza os demais.
 */
export function reconcileConnectorsAfterDrag(
  blocks: ComunicadoBlock[],
  draggedIds: ReadonlySet<string>,
): ComunicadoBlock[] {
  const next = blocks.map((block) => {
    if (!draggedIds.has(block.id) || !isConnectorShapeBlock(block)) return block;
    return detachConnector(block);
  });
  return syncAllConnectors(next);
}
