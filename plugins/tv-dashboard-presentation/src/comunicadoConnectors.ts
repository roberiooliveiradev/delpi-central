/**
 * Conectores entre blocos — linha reta ligada a âncoras (estilo PowerPoint).
 * Endpoints vivem em `vertices` + `frame`; `connector` guarda a ligação (parcial ou total).
 */

import type {
  ComunicadoBlock,
  ComunicadoConnectorRouting,
  ComunicadoGeometryVertex,
  ComunicadoShapeBlock,
  ComunicadoShapeConnector,
} from "./comunicadoTypes";
import { pickNearestAnchorsBetweenBlocks } from "./comunicadoConnectionSites";
import {
  buildCurveControlPoint,
  buildRoutedLinePoints,
  normalizeConnectorRouting,
} from "./comunicadoConnectorRouting";
import {
  applyLinePolyline,
  geometryBoundingFrame,
  resolveLineEndpoints,
} from "./comunicadoShapeGeometry";
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

function trimId(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

/**
 * Aceita ligação total (from+to) ou parcial (só um lado — ponta livre no outro).
 */
export function normalizeShapeConnector(value: unknown): ComunicadoShapeConnector | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const fromBlockId = trimId(raw.fromBlockId) || undefined;
  const toBlockId = trimId(raw.toBlockId) || undefined;
  if (!fromBlockId && !toBlockId) return undefined;
  if (fromBlockId && toBlockId && fromBlockId === toBlockId) return undefined;
  const routing = normalizeConnectorRouting(raw.routing);
  return {
    ...(fromBlockId ? { fromBlockId } : {}),
    ...(toBlockId ? { toBlockId } : {}),
    fromAnchor: normalizeConnectorAnchor(raw.fromAnchor),
    toAnchor: normalizeConnectorAnchor(raw.toAnchor),
    ...(routing !== "straight" ? { routing } : {}),
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
      (block.connector.fromBlockId || block.connector.toBlockId),
  );
}

/** Ponto de âncora (% do palco) a partir do frame do bloco. */
export function resolveBlockAnchorPoint(
  block: ComunicadoBlock,
  anchor: ComunicadoConnectorAnchor = "center",
): ComunicadoGeometryVertex {
  const { x, y, w, h } = block.frame;
  // Ponto: frame canônico w=h=0 na posição.
  if (block.type === "shape" && w === 0 && h === 0) {
    return { x, y };
  }
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
  fallback?: [ComunicadoGeometryVertex, ComunicadoGeometryVertex],
): [ComunicadoGeometryVertex, ComunicadoGeometryVertex] | null {
  const from = connector.fromBlockId
    ? blocks.find((block) => block.id === connector.fromBlockId)
    : undefined;
  const to = connector.toBlockId
    ? blocks.find((block) => block.id === connector.toBlockId)
    : undefined;

  const fb = fallback ?? null;
  const start = from
    ? resolveBlockAnchorPoint(from, normalizeConnectorAnchor(connector.fromAnchor))
    : fb?.[0];
  const end = to
    ? resolveBlockAnchorPoint(to, normalizeConnectorAnchor(connector.toAnchor))
    : fb?.[1];

  if (!start || !end) return null;
  return [start, end];
}

/** Atualiza vertices + frame de um bloco conector a partir dos alvos atuais. */
export function applyConnectorGeometry(
  lineBlock: ComunicadoShapeBlock,
  blocks: ComunicadoBlock[],
): ComunicadoShapeBlock {
  const connector = normalizeShapeConnector(lineBlock.connector);
  if (!connector) {
    if (!lineBlock.connector) return lineBlock;
    const { connector: _drop, ...rest } = lineBlock;
    return rest as ComunicadoShapeBlock;
  }

  const current = resolveLineEndpoints(lineBlock);
  const endpoints = resolveConnectorEndpoints(blocks, connector, current);
  if (!endpoints) {
    const { connector: _drop, ...rest } = lineBlock;
    return rest as ComunicadoShapeBlock;
  }

  // Alvo ausente → solta só aquele lado.
  let nextConnector: ComunicadoShapeConnector | undefined = { ...connector };
  if (connector.fromBlockId && !blocks.some((block) => block.id === connector.fromBlockId)) {
    const { fromBlockId: _f, ...rest } = nextConnector;
    nextConnector = rest;
  }
  if (connector.toBlockId && !blocks.some((block) => block.id === connector.toBlockId)) {
    const { toBlockId: _t, ...rest } = nextConnector!;
    nextConnector = rest;
  }
  nextConnector = normalizeShapeConnector(nextConnector);

  const [a, b] = endpoints;
  const routing = normalizeConnectorRouting(nextConnector?.routing ?? connector.routing);
  const fromAnchor = normalizeConnectorAnchor(nextConnector?.fromAnchor ?? connector.fromAnchor);
  const toAnchor = normalizeConnectorAnchor(nextConnector?.toAnchor ?? connector.toAnchor);
  const routePoints = buildRoutedLinePoints(a, b, routing, fromAnchor, toAnchor);
  let withEnds = applyLinePolyline(lineBlock, routePoints);
  if (routing === "curve") {
    const control = buildCurveControlPoint(a, b);
    withEnds = {
      ...withEnds,
      frame: geometryBoundingFrame({ primitive: "line", points: [a, control, b] }),
    };
  }
  if (!nextConnector) {
    const { connector: _drop, ...rest } = withEnds;
    return rest as ComunicadoShapeBlock;
  }
  return {
    ...withEnds,
    connector: {
      ...nextConnector,
      ...(routing !== "straight" ? { routing } : {}),
    },
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
  if (a.type === "shape" && isLineShapeKind(a.shape)) return false;
  if (b.type === "shape" && isLineShapeKind(b.shape)) return false;
  return true;
}

export function createConnectorBlock(
  from: ComunicadoBlock,
  to: ComunicadoBlock,
  options?: {
    shape?: "line" | "line-arrow-right" | "line-arrow-left" | "line-arrow-both";
    zIndex?: number;
    fromAnchor?: ComunicadoConnectorAnchor;
    toAnchor?: ComunicadoConnectorAnchor;
    routing?: ComunicadoConnectorRouting;
  },
): ComunicadoShapeBlock {
  const shape = options?.shape ?? "line-arrow-right";
  const nearest = pickNearestAnchorsBetweenBlocks(from, to);
  const routing = normalizeConnectorRouting(options?.routing);
  const connector: ComunicadoShapeConnector = {
    fromBlockId: from.id,
    toBlockId: to.id,
    fromAnchor: options?.fromAnchor ?? nearest.fromAnchor ?? "center",
    toAnchor: options?.toAnchor ?? nearest.toAnchor ?? "center",
    ...(routing !== "straight" ? { routing } : {}),
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

/** Remove ligação completa. */
export function detachConnector(block: ComunicadoShapeBlock): ComunicadoShapeBlock {
  if (!block.connector) return block;
  const { connector: _drop, ...rest } = block;
  return rest as ComunicadoShapeBlock;
}

/**
 * Solta só uma ponta (0 = from, 1 = to). A outra permanece grudada se existir.
 */
export function detachConnectorEndpoint(
  block: ComunicadoShapeBlock,
  endpointIndex: 0 | 1,
): ComunicadoShapeBlock {
  const connector = normalizeShapeConnector(block.connector);
  if (!connector) return block;
  const routing = connector.routing;
  const next: ComunicadoShapeConnector =
    endpointIndex === 0
      ? {
          ...(connector.toBlockId ? { toBlockId: connector.toBlockId } : {}),
          toAnchor: connector.toAnchor,
          fromAnchor: connector.fromAnchor,
          ...(routing ? { routing } : {}),
        }
      : {
          ...(connector.fromBlockId ? { fromBlockId: connector.fromBlockId } : {}),
          fromAnchor: connector.fromAnchor,
          toAnchor: connector.toAnchor,
          ...(routing ? { routing } : {}),
        };
  const normalized = normalizeShapeConnector(next);
  if (!normalized) return detachConnector(block);
  return { ...block, connector: normalized };
}

/**
 * Gruda uma ponta a um site (cria/atualiza connector parcial ou total).
 */
export function attachConnectorEndpoint(
  block: ComunicadoShapeBlock,
  endpointIndex: 0 | 1,
  targetBlockId: string,
  anchor: ComunicadoConnectorAnchor = "center",
): ComunicadoShapeBlock {
  const current = normalizeShapeConnector(block.connector) ?? {};
  const next: ComunicadoShapeConnector =
    endpointIndex === 0
      ? {
          ...current,
          fromBlockId: targetBlockId,
          fromAnchor: anchor,
          ...(current.toBlockId ? { toBlockId: current.toBlockId } : {}),
          toAnchor: current.toAnchor,
        }
      : {
          ...current,
          toBlockId: targetBlockId,
          toAnchor: anchor,
          ...(current.fromBlockId ? { fromBlockId: current.fromBlockId } : {}),
          fromAnchor: current.fromAnchor,
        };
  const normalized = normalizeShapeConnector(next);
  if (!normalized) return block;
  return { ...block, connector: normalized };
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

/** Após apagar blocos: remove conectores sem nenhum alvo restante; sync parcial senão. */
export function pruneOrphanConnectors(blocks: ComunicadoBlock[]): ComunicadoBlock[] {
  const ids = new Set(blocks.map((block) => block.id));
  return blocks
    .filter((block) => {
      if (!isConnectorShapeBlock(block)) return true;
      const fromOk = !block.connector.fromBlockId || ids.has(block.connector.fromBlockId);
      const toOk = !block.connector.toBlockId || ids.has(block.connector.toBlockId);
      return fromOk || toOk;
    })
    .map((block) => {
      if (!isConnectorShapeBlock(block)) return block;
      return applyConnectorGeometry(block, blocks);
    });
}

/**
 * Após mover o bloco linha inteiro: desliga conectores arrastados e sincroniza os demais.
 * Drag de endpoint NÃO deve passar por aqui (usa attach/detach parcial).
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
