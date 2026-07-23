/**
 * Connection sites (âncoras) estilo PowerPoint — pontos onde linhas/conectores grudam.
 */

import type {
  ComunicadoBlock,
  ComunicadoGeometryVertex,
  ComunicadoShapeConnector,
} from "./comunicadoTypes";
import { resolveShapeGeometry } from "./comunicadoShapeGeometry";
import { isConnectorShapeBlock, type ComunicadoConnectorAnchor } from "./comunicadoConnectors";
import { isLineShapeKind, isPointShapeKind } from "./comunicadoVisualPrimitive";

export type ConnectionSiteId = ComunicadoConnectorAnchor;

export type ConnectionSite = {
  blockId: string;
  id: ConnectionSiteId;
  x: number;
  y: number;
};

/** Distância máxima (% do palco) para snap ao soltar/arrastar ponta. */
export const CONNECTION_SITE_SNAP_PCT = 3.5;

const SITE_ORDER: ConnectionSiteId[] = ["n", "e", "s", "w", "center"];

function siteFromFrame(
  blockId: string,
  frame: { x: number; y: number; w: number; h: number },
  id: ConnectionSiteId,
): ConnectionSite {
  const { x, y, w, h } = frame;
  switch (id) {
    case "n":
      return { blockId, id, x: x + w / 2, y };
    case "s":
      return { blockId, id, x: x + w / 2, y: y + h };
    case "w":
      return { blockId, id, x, y: y + h / 2 };
    case "e":
      return { blockId, id, x: x + w, y: y + h / 2 };
    case "center":
    default:
      return { blockId, id, x: x + w / 2, y: y + h / 2 };
  }
}

/** Blocos que podem receber pontas de conector. */
export function blockAcceptsConnectionSites(block: ComunicadoBlock): boolean {
  if (isConnectorShapeBlock(block)) return false;
  if (block.type === "shape" && isLineShapeKind(block.shape)) return false;
  return true;
}

/**
 * Sites N/S/E/W/centro no frame do bloco.
 * Ponto: só centro na posição do marcador.
 */
export function resolveBlockConnectionSites(block: ComunicadoBlock): ConnectionSite[] {
  if (!blockAcceptsConnectionSites(block)) return [];

  if (block.type === "shape" && isPointShapeKind(block.shape)) {
    const geometry = resolveShapeGeometry(block);
    if (geometry.primitive !== "point") return [];
    return [
      {
        blockId: block.id,
        id: "center",
        x: geometry.position.x,
        y: geometry.position.y,
      },
    ];
  }

  return SITE_ORDER.map((id) => siteFromFrame(block.id, block.frame, id));
}

export function resolveAllConnectionSites(
  blocks: ComunicadoBlock[],
  options?: { excludeBlockIds?: ReadonlySet<string> },
): ConnectionSite[] {
  const exclude = options?.excludeBlockIds;
  const sites: ConnectionSite[] = [];
  for (const block of blocks) {
    if (exclude?.has(block.id)) continue;
    sites.push(...resolveBlockConnectionSites(block));
  }
  return sites;
}

export function distancePct(
  a: ComunicadoGeometryVertex,
  b: ComunicadoGeometryVertex,
): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

/** Site mais próximo dentro do limiar (ou null). */
export function findNearestConnectionSite(
  point: ComunicadoGeometryVertex,
  blocks: ComunicadoBlock[],
  options?: {
    excludeBlockIds?: ReadonlySet<string>;
    maxDistancePct?: number;
  },
): ConnectionSite | null {
  const max = options?.maxDistancePct ?? CONNECTION_SITE_SNAP_PCT;
  let best: ConnectionSite | null = null;
  let bestDist = max;
  for (const site of resolveAllConnectionSites(blocks, {
    excludeBlockIds: options?.excludeBlockIds,
  })) {
    const dist = distancePct(point, site);
    if (dist <= bestDist) {
      best = site;
      bestDist = dist;
    }
  }
  return best;
}

/**
 * Escolhe âncoras mais próximas entre dois blocos (ribbon «Conectar»).
 * Preferência: par de sites com menor distância (não só centros).
 */
export function pickNearestAnchorsBetweenBlocks(
  from: ComunicadoBlock,
  to: ComunicadoBlock,
): Pick<ComunicadoShapeConnector, "fromAnchor" | "toAnchor"> {
  const fromSites = resolveBlockConnectionSites(from);
  const toSites = resolveBlockConnectionSites(to);
  if (fromSites.length === 0 || toSites.length === 0) {
    return { fromAnchor: "center", toAnchor: "center" };
  }
  let bestFrom: ConnectionSiteId = "center";
  let bestTo: ConnectionSiteId = "center";
  let bestDist = Number.POSITIVE_INFINITY;
  for (const a of fromSites) {
    for (const b of toSites) {
      const dist = distancePct(a, b);
      if (dist < bestDist) {
        bestDist = dist;
        bestFrom = a.id;
        bestTo = b.id;
      }
    }
  }
  return { fromAnchor: bestFrom, toAnchor: bestTo };
}
